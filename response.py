from nlu import interpret_text
from retriever import retrieve_info # Adı artık retriever.py
from semantic_engine import SemanticEngine # Yeni: Semantic Beyin
from generator import LocalGenerator #Hafta11
import re
import logging
from logger import log_event

# --- Global Initialization (Singleton) ---
# Modeli her sorguda tekrar yüklememek için global alanda bir kere başlatıyoruz.
try:
    print("Semantic Engine (Anlama) yukleniyor...")
    semantic_brain = SemanticEngine()
except Exception as e:
    log_event("CRITICAL", f"Semantic Engine Baslatilamadi: {e}", "response")
    semantic_brain = None

def build_dynamic_instruction(memory):
    """
    Hafızadan profil bilgilerini çeker ve mBART için talimat hazırlar.
    Profil boşsa varsayılan talimatı döner.
    """
    profile = memory.get_profile() # memory.py'de yazdığımız fonksiyon
    
    if not profile:
        return "Bu metni Türkçe olarak özetle."

    # Profil bilgilerini metne döküyoruz
    user_name = profile.get("user_name", "Kullanıcı")
    expertise = profile.get("expertise", "genel")
    tone = profile.get("tone", "sade")

    # mBART'a giden dinamik talimat (Instruction)
    return f"Kullanıcı adı {user_name}. Bilgi seviyesi {expertise}. Üslup {tone}. Bu metni bu profile uygun şekilde Türkçe özetle."

try:
    print("mBART Generator (Uretim) yukleniyor...")
    brain_generator = LocalGenerator()
except Exception as e:
    log_event("CRITICAL", f"Generator Engine Baslatilamadi: {e}", "response")
    brain_generator = None

def generate_response(user_input: str, memory, tool_manager) -> str: # Hafta5: tool_manager
    """
    Kullanıcı girdisini analiz eder ve cevabı oluşturur.
    Akış: NLU -> (Komut / Sorgu / Sohbet) -> (LTM Exact -> LTM Semantic -> API)
    """
    try:
        # 1. NLU Analizi
        analysis = interpret_text(user_input)
        intent = analysis["intent"]

        #Hafta13: Geri bildirim ve adaptasyon(dinamik üslup)
        if intent == "feedback_style":
            new_tone = analysis.get("value")
            memory.set_profile("tone",new_tone)
            return f"Anladım. Üslubumu '{new_tone}' olarak güncelledim. Bundan sonra böyle konuşacağım" 

        # ---------------------------------------------------------
        # 1. NİYET: KOMUT (Hafta 6-13 Güncellendi)
        # ---------------------------------------------------------
        if intent == "command":
            tool_key = analysis.get("tool_key") 
            payload = analysis.get("payload")

            # 'çık' komutu (main.py zaten yakalıyor ama NLU'da da var)
            if tool_key:
                # --- KRİTİK GÜNCELLEME (V2) ---
                # Artık 'find_tool_for_command' ÇAĞIRMIYORUZ.
                # Doğrudan 'execute_tool'u 'tool_key' ile çağırıyoruz.
                #Hafta13: Özel komut - unut/temizle
                #NLU dan gelen 'forget_last' tool_key'ini yakalayıp memory'deki silgiyi tetikler.

                if tool_key == "forget_last":
                    #Hafızadan son kaydo silme mantığı buraya gelebilir
                    success = memory.delete_last_memory() #memory.py 'de yazdığımız fonksiyon
                    if success:
                        return "Son etkileşimi hafızamdan sildim ve unuttum."
                    else:
                        return "Hafızayo temizlerken teknik bir sorun oluştu"

                result = tool_manager.execute_tool(tool_key, payload)
                
                # Not: Komutların sonucunu interactions'a kaydedebiliriz
                # memory.save_interaction(user_input, result) 
                return result
            else:
                # Niyet "command" ama NLU uygun 'tool_key' bulamadı
                response_text = "Komutunuzu anladım ancak bu eylemi gerçekleştirecek uygun bir araç bulamadım."
                memory.save_interaction(user_input, response_text)
                return response_text
        # ---------------------------------------------------------
        # 1.1 NİYET: PROFİL GÜNCELLEME (HAFTA 12)
        # ---------------------------------------------------------
        elif intent == "profile_update":
            # NLU'dan gelen key (ayar adı) ve value (yeni değer)
            key = analysis.get("key")
            value = analysis.get("value")
            
            # Veritabanına kaydet (TXT aynası otomatik güncellenir)
            success = memory.set_profile(key, value)
            
            if success:
                response_text = f"Tamamdır, '{key}' bilgisini '{value}' olarak güncelledim."
                return response_text
            else:
                return "Profil güncellenirken teknik bir sorun oluştu."

        # ---------------------------------------------------------
        # 2. NİYET: SORGULAMA (HAFTA 13 Hassas AYAR)
        # ---------------------------------------------------------
        elif intent == "query":
            # ADIM A: Önce Tam Eşleşme (Exact Match) - En Hızlısı
            # Kullanıcı daha önce "Japonya nedir" sorduysa, hafızadan direkt gelir.
            exact_match = memory.read_from_memory(user_input)
            if exact_match:
                log_event("INFO", "Cevap LTM'den (Tam Eslesme) dondu.", "response")
                memory.save_interaction(user_input, exact_match)
                return f"{exact_match} (Hafızadan)"
            
            # ADIM B: Semantik Arama (Semantic Match) - Akıllı Hafıza (Hafta 9)
            # "Çizme ülke" deyince "İtalya"yı bulması için.
            #Hafta 13 iyileştirme 
            if semantic_brain:
                try:
                    #HAFTA13: KApsamı son 50 geçerli kayıtla sınıyoruz
                    # 1. Tüm hafızayı çek (Corpus)
                    memory.cursor.execute("SELECT value FROM memory WHERE status = 'valid' ORDER BY created_at DESC LIMIT 50")
                    # fetchall() liste içinde tuple döndürür, text'i almak için row[0] diyoruz
                    all_memories = [row[0] for row in memory.cursor.fetchall()]
                    
                    if all_memories:
                        # 2. Beyne sor
                        best_match, score = semantic_brain.find_best_match(user_input, all_memories)
                        
                        # 3. Eşik Değer Kontrolü (0.35 Güven Skoru - Test için düşürdük)
                        #HAFTA13: Eşik değeri 70 e alındı
                        # Skor 0.75 üzerindeyse kelime kontrolüne bakmadan kabul et (Güçlü eşleşme)
                        # Skor 0.60 - 0.75 arasındaysa en az 1 tane önemli kelime uyuşmalı

                        if score >= 0.75:
                            return f"{best_match}\n\n*(Hafıza Skoru: %{int(score*100)})*"
                        
                        elif score >= 0.60:
                            important_words = [w for w in user_input.lower().split() if len(w) > 3]
                            if any(w in best_match.lower() for w in important_words):
                                return f"{best_match}\n\n*(Anlamsal Hafıza: %{int(score*100)})*"
                except Exception as e:
                    log_event("ERROR", f"Semantik Arama Hatasi: {e}", "response")
                    # Hata olursa akışı kesme, API'ye devam et.
            
            # ADIM C: Dış Kaynak (API / İnternet) - Fallback + MBART HAFTA 12
        
            log_event("INFO", "Hafizada bulunamadi, API'ye gidiliyor...", "response")
            raw_result = retrieve_info(user_input, memory)
            # mBART Devreye Giriyor
            if brain_generator and raw_result and len(raw_result) > 100 and "Sorun var" not in raw_result:
                log_event("INFO", "Veri mBART ve Profil ile isleniyor...", "response")
                
                # Dinamik talimatı oluştur (Hafta 12)
                instruction = build_dynamic_instruction(memory)
                
                # mBART üretimi yap
                processed_response = brain_generator.generate(raw_result, instruction)
                
                # HAFTA 13: PASİF PROFİLLEME (Gözlem)
                # Kullanıcı cümle içinde "severim, ilgi duyuyorum" gibi şeyler dediyse not al
                if "severim" in user_input.lower() or "sevdiğim" in user_input.lower():
                    # Zarf temizleme mantığı eklendi
                    parts = user_input.lower().split()
                    adverbs = ["çok", "en", "daha", "gerçekten", "aşırı", "fazla"]
                    clean_parts = [w for w in parts if w not in adverbs]
                    
                    target = "severim" if "severim" in clean_parts else "sevdiğim"
                    if target in clean_parts:
                        idx = clean_parts.index(target)
                        if idx >= 2:
                            interest = f"{clean_parts[idx-2]} {clean_parts[idx-1]}"
                        elif idx == 1:
                            interest = clean_parts[0]
                        else:
                            interest = "bilinmiyor"
                        memory.set_profile("ilgi_alani", interest)
                
                final_output = f"{processed_response}\n\n*(Profilinize göre mBART tarafından özetlendi)*"
                memory.save_interaction(user_input, final_output)
                return final_output
            
            else:
                memory.save_interaction(user_input, raw_result)
                return raw_result
            
        # --- HAFTA 13: NİYET AYRIMI - KİŞİSEL SOHBET VE PASİF GÖZLEMCİ ---
        elif intent == "chat":
            # --- HAFTA 13: NESNE AYRIŞTIRICI (Yemek, Renk, Hobi) ---
            text_low = user_input.lower()
            parts = text_low.split()
            adverbs = ["çok", "en", "daha", "gerçekten", "aşırı", "fazla"]
            clean_parts = [w for w in parts if w not in adverbs]

            # 1. Yemek Yakalayıcı
            if "yemek" in text_low:
                # "en sevdiğim yemek mantıdır" -> "mantı"
                match = re.search(r"(?:yemek|yemeğim)\s+([\w\s]+?)(?:\s|dır|dir|tır|tir|$)", text_low)
                if match:
                    memory.set_profile("favori_yemek", match.group(1).strip())
            
            # 2. Renk Yakalayıcı (Dengim/Rengim hatası dahil)
            elif any(r in text_low for r in ["renk", "rengim", "dengim", "denk"]):
                match = re.search(r"(?:renk|rengim|dengim|denk)\s+([\w\s]+?)(?:\s|dır|dir|tır|tir|$)", text_low)
                if match:
                    memory.set_profile("favori_renk", match.group(1).strip())

            # 3. Genel İlgi Alanı Yakalayıcı
            elif "severim" in text_low or "sevdiğim" in text_low:
                target = "severim" if "severim" in clean_parts else "sevdiğim"
                if target in clean_parts:
                    idx = clean_parts.index(target)
                    if idx >= 2:
                        interest = f"{clean_parts[idx-2]} {clean_parts[idx-1]}"
                    elif idx == 1:
                        interest = clean_parts[0]
                    else:
                        interest = "bilinmiyor"
                    memory.set_profile("ilgi_alani", interest)

            response_text = "Bunu öğrendiğim iyi oldu Yavuz, notlarımı aldım."
            memory.save_interaction(user_input, response_text)
            return response_text

        # ---------------------------------------------------------
        # 3. NİYET: GENEL SOHBET (Hafta 1-2-13 Pasif Gözlemci Dahil)
        # ---------------------------------------------------------
        elif "merhaba" in user_input.lower():
            response_text = "Merhaba! Size nasıl yardımcı olabilirim?"
            memory.save_interaction(user_input, response_text)
            return response_text

        elif "nasılsın" in user_input.lower():
            response_text = "İyiyim, teşekkür ederim. Hafızam ve Semantik motorum aktif."
            memory.save_interaction(user_input, response_text)
            return response_text

        # ---------------------------------------------------------
        # 4. VARSAYILAN (Fallback)
        # ---------------------------------------------------------
        else:
            # NLU 'query' dememiş olsa bile, kullanıcı bir şey sormuş olabilir.
            # "Emin değilim" demek yerine şansımızı internette deniyoruz.
            log_event("INFO", "Niyet belirsiz, son care internete gidiliyor...", "response")
            result = retrieve_info(user_input, memory)
            
            memory.save_interaction(user_input, result)
            return result
            
    except Exception as e:
        error_msg = f"Sistem Hatasi: {e}"
        log_event("CRITICAL", error_msg, "response")
        return error_msg