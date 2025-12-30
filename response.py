from nlu import interpret_text
from retriever import retrieve_info # Adı artık retriever.py
from semantic_engine import SemanticEngine # Yeni: Semantic Beyin
from generator import LocalGenerator #Hafta11
import logging
from logger import log_event

# --- Global Initialization (Singleton) ---
# Modeli her sorguda tekrar yüklememek için global alanda bir kere başlatıyoruz.
try:
    print("⏳ Semantic Engine (Anlama) yükleniyor...")
    semantic_brain = SemanticEngine()
except Exception as e:
    log_event("CRITICAL", f"Semantic Engine Başlatılamadı: {e}", "response")
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
    print("⏳ mBART Generator (Üretim) yükleniyor...")
    brain_generator = LocalGenerator()
except Exception as e:
    log_event("CRITICAL", f"Generator Engine Başlatılamadı: {e}", "response")
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

        # ---------------------------------------------------------
        # 1. NİYET: KOMUT (Hafta 6 Güncellendi)
        # ---------------------------------------------------------
        if intent == "command":
            tool_key = analysis.get("tool_key")
            payload = analysis.get("payload")

            # 'çık' komutu (main.py zaten yakalıyor ama NLU'da da var)
            if tool_key:
                # --- KRİTİK GÜNCELLEME (V2) ---
                # Artık 'find_tool_for_command' ÇAĞIRMIYORUZ.
                # Doğrudan 'execute_tool'u 'tool_key' ile çağırıyoruz.
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
        # 2. NİYET: SORGULAMA (Hafta 3-4 ve Hafta 9 Semantik)
        # ---------------------------------------------------------
        elif intent == "query":
            # ADIM A: Önce Tam Eşleşme (Exact Match) - En Hızlısı
            # Kullanıcı daha önce "Japonya nedir" sorduysa, hafızadan direkt gelir.
            exact_match = memory.read_from_memory(user_input)
            if exact_match:
                log_event("INFO", "Cevap LTM'den (Tam Eşleşme) döndü.", "response")
                memory.save_interaction(user_input, exact_match)
                return f"{exact_match} (Hafızadan)"
            
            # ADIM B: Semantik Arama (Semantic Match) - Akıllı Hafıza (Hafta 9)
            # "Çizme ülke" deyince "İtalya"yı bulması için.
            if semantic_brain:
                try:
                    # 1. Tüm hafızayı çek (Corpus)
                    memory.cursor.execute("SELECT value FROM memory WHERE status = 'valid'")
                    # fetchall() liste içinde tuple döndürür, text'i almak için row[0] diyoruz
                    all_memories = [row[0] for row in memory.cursor.fetchall()]
                    
                    if all_memories:
                        # 2. Beyne sor
                        best_match, score = semantic_brain.find_best_match(user_input, all_memories)
                        
                        # 3. Eşik Değer Kontrolü (0.35 Güven Skoru - Test için düşürdük)
                        if score >= 0.60:
                            response_text = f"{best_match}\n\n*(Anlamsal Hafıza Skoru: %{int(score*100)})*"
                            log_event("INFO", f"Cevap LTM'den (Semantik: {score:.2f}) döndü.", "response")
                            memory.save_interaction(user_input, response_text)
                            return response_text
                    
                except Exception as e:
                    log_event("ERROR", f"Semantik Arama Hatası: {e}", "response")
                    # Hata olursa akışı kesme, API'ye devam et.
            
            # ADIM C: Dış Kaynak (API / İnternet) - Fallback + MBART HAFTA 12
        
            log_event("INFO", "Hafızada bulunamadı, API'ye gidiliyor...", "response")
            raw_result =retrieve_info(user_input,memory)
            # mBART Devreye Giriyor
            if brain_generator and raw_result and len(raw_result) > 100 and "Sorun var" not in raw_result:
                log_event("INFO", "Veri mBART ve Profil ile işleniyor...", "response")
                
                # Dinamik talimatı oluştur (Hafta 12)
                instruction = build_dynamic_instruction(memory)
                
                # mBART üretimi yap
                processed_response = brain_generator.generate(raw_result, instruction)
                
                final_output = f"{processed_response}\n\n*(Profilinize göre mBART tarafından özetlendi)*"
                memory.save_interaction(user_input, final_output)
                return final_output
            
            else:
                memory.save_interaction(user_input, raw_result)
                return raw_result

        # ---------------------------------------------------------
        # 3. NİYET: GENEL SOHBET (Hafta 1-2)
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
            log_event("INFO", "Niyet belirsiz, son çare internete gidiliyor...", "response")
            result = retrieve_info(user_input, memory)
            
            memory.save_interaction(user_input, result)
            return result
            
    except Exception as e:
        error_msg = f"Sistem Hatası: {e}"
        log_event("CRITICAL", error_msg, "response")
        return error_msg