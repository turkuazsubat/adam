import spacy
import re # Düzenli ifadeler için gerekli

# Model yükleme
try:
    nlp = spacy.load("en_core_web_sm") 
except:
    # Eğer model yoksa hata vermesin, basic çalışsın
    import sys
    print("Spacy modeli bulunamadı, 'python -m spacy download en_core_web_sm' yapmalısın.")
    nlp = lambda x: x # Dummy

def clean_payload(text: str, triggers: list) -> str:
    text_lower = text.lower().strip()
    for trigger in triggers:
        if text_lower.endswith(trigger):
            return text[:-len(trigger)].strip()
        # Bazı durumlarda trigger başta olabilir (Örn: "Başlat spotify")
        if text_lower.startswith(trigger):
            return text[len(trigger):].strip()
    return text

def interpret_text(text: str):
    # Dummy nlp kontrolü
    if hasattr(nlp, "pipe"): 
        doc = nlp(text)
        keywords = [token.lemma_.lower() for token in doc if token.is_alpha]
        entities = [(ent.text, ent.label_) for ent in doc.ents]
    else:
        # Spacy yoksa manuel basit split
        keywords = text.lower().split()
        entities = []
    
    raw_text = text
    text_lower = text.lower().strip()
    intent = "general" 
    tool_key = None 
    payload = raw_text
    
    # --- HAFTA 12: PROFIL GÜNCELLEME YAKALAYICI (ÖNCELİKLİ) ---
    
    # 1. İsim Güncelleme (Örn: "Adım Yavuz", "Bana Kaptan de")
    # Hafta 13 Fix: Regex açgözlü (greedy) hale getirildi ve Türkçe karakterler eklendi.
    name_match = re.search(r"(?:adım|ismim|bana)\s+([a-zA-ZçğıöşüÇĞİÖŞÜ\s]+)(?:\s+olsun|\s+de|$)", text_lower)
    if name_match:
        return {
            "intent": "profile_update",
            "key": "user_name",
            "value": name_match.group(1).strip().capitalize(),
            "keywords": keywords, "entities": entities
        }

    # 2. Üslup Güncelleme (Örn: "Üslubun sert olsun")
    tone_match = re.search(r"(?:üslubun|tavrın|konuşman)\s+([a-zA-ZçğıöşüÇĞİÖŞÜ\s]+)(?:\s+olsun|$)", text_lower)
    if tone_match:
        return {
            "intent": "profile_update",
            "key": "tone",
            "value": tone_match.group(1).strip(),
            "keywords": keywords, "entities": entities
        }
    
    # Hafta 13: Unutma/Silme Komutu yakalayıcı
    # [WEEK 13 FIX]: "Silgi" kelimesinin "sil" komutunu tetiklememesi için 'keywords' (kök) listesine bakıyoruz.
    # Ayrıca 'nedir' koruması eklendi.
    if (any(word in keywords for word in ["unut", "sil"]) or "hafızandan çıkar" in text_lower):
        if "nedir" not in text_lower: # Eğer soru soruyorsa silme işlemi yapma
            return {
                "intent": "command",
                "tool_key": "forget_last",
                "payload": None,
                "keywords": keywords, "entities": entities
            }
    
    # --- HAFTA 13: ÜSLUP GERİ BİLDİRİMİ (FEEDBACK LOOP) ---
    style_match = re.search(r"([\w\s]+?)\s+(?:anlat|konuş|yaz)", text_lower)
    if style_match and any(w in text_lower for w in ["daha", "biraz"]):
        return {
            "intent": "feedback_style",
            "value": style_match.group(1).strip(),
            "keywords": keywords, "entities": entities
        }

    # --- HAFTA 13: KİŞİSEL İFADE VE GÖZLEM AYRIMI (PASİF ANALİZ) ---
    # Hafta 13 Fix: 'renk' ve 'favori' gibi kelimeler eklendi, query'den önce yakalanması sağlandı.
    # Fix: 'denk', 'yemek', 'hobi' gibi kelimeler ve yazım hataları eklendi.
    personal_keywords = ["severim", "sevmem", "hoşlanırım", "hoşlanmam", "ilgi", "sevdiğim", "en sevdiğim", "favori", "rengim", "renk", "dengim", "denk", "yemek"]
    
    # [WEEK 13 FIX]: Regex \b (word boundary) ile kelime sınırı eklendi. 
    # Artık "Ahenk" içinde "renk" veya "Hemoglobin" içinde "hem" bulunmayacak.
    pattern = r"\b(?:" + "|".join(personal_keywords) + r")\b"
    
    if re.search(pattern, text_lower):
        return {
            "intent": "chat",
            "tool_key": None,
            "payload": raw_text,
            "keywords": keywords, "entities": entities
        }
    
    #Hafta 14 Masaüstü otomasyon komutları
    
    #1. Pano(Clipboard Okuma)
    #"Panoyu oku", "Kopyaladığın şey ne", "Panodaki hatayı açıkla"

    if "pano" in text_lower or "kopya" in text_lower or "clipboard" in text_lower:
        return {
            "intent": "command",
            "tool_key": "clipboard_read", # tools/clipboard_tool.py
            "payload": None,
            "keywords": keywords, "entities": entities
        }

    # 2. Uygulama Başlatma (Launcher)
    # "Spotify'ı aç", "brave başlat", "Hesap makinesini çalıştır"

    launch_triggers = ["aç", "başlat", "çalıştır"]
    if any(trig in text_lower for trig in launch_triggers):
        if len(text.split()) > 1: 
            target_app = clean_payload(raw_text, launch_triggers)
            
            # [WEEK 14 FIX] Ek Temizliği (Suffix Removal)
            # Türkçe belirtme eklerini (ı, i, u, ü) sondan temizle
            # Örn: "Spotifyı" -> "Spotify", "Notepadi" -> "Notepad"
            target_app = target_app.replace("'ı", "").replace("'i", "").replace("'u", "").replace("'ü", "") # Kesme işaretliler
            if target_app[-1] in ["ı", "i", "u", "ü"]: # Bitişik yazılanlar
                target_app = target_app[:-1]
            
            return {
                "intent": "command",
                "tool_key": "app_launcher",
                "payload": target_app.strip(),
                "keywords": keywords, "entities": entities
            }
    
    #3. PDF Döküman Okuma
    #"tez.pdf" dosyasını oku","notlar.pdf analiz et"
    if ".pdf" in text_lower:
        # ".pdf" kelimesini içeren kelimeyi bul (dosya adı)
        words = text.split()
        filename = next((w for w in words if ".pdf" in w.lower()), None) 
    
        if filename:
            return{
                "intent":"command",
                "tool_key": "pdf_reader", #tools/document_tool.py
                "payload":filename,
                "keywords":keywords, "entities":entities
            }

    # --- HAFTA 15: OCR / GÖRÜNTÜ OKUMA ---
    # "Resmi oku", "Ekranı oku", "OCR yap"
    ocr_triggers = ["resmi oku", "ekranı oku", "görüntüyü oku", "ocr"]
    if any(trig in text_lower for trig in ocr_triggers):
        return {
            "intent": "command",
            "tool_key": "ocr_read", # ToolManager'da tanımladığımız vision.py
            "payload": None, # Panodaki resmi okuyacağı için payload yok
            "keywords": keywords, "entities": entities
        }
    # -------------------------------------

    # --- ESKİ MANTIK DEVAM EDİYOR ---
    if raw_text.startswith("!"):
        intent = 'feedback'

    elif "not" in keywords and "al" in keywords:
        intent = "command"
        tool_key = "note"
        payload = clean_payload(raw_text, ["not al","notunu al"])

    elif ("görev" in keywords and "ekle" in keywords) or \
         ("yapılacak" in keywords and "ekle" in keywords):
        intent = "command"
        tool_key = "todo_add"
        payload = clean_payload(raw_text, ["görev ekle", "yapılacaklara ekle", "listeye ekle", "ekle"])

    elif ("görev" in keywords or "yapılacak" in keywords) and \
         any(k.startswith("liste") for k in keywords):
        intent = "command"
        tool_key = "todo_list"
        payload = None 

    elif raw_text.lower() in ["çık","exit","quit"]:
        intent ="command"
        tool_key = "exit"

    elif ("nedir" in text_lower or 
          "ara" in text_lower or 
          "bilgi" in text_lower or 
          "bahseder" in text_lower or 
          "?" in text or 
          len(text.split()) >= 3):
        intent = "query"
    
    return {
        "intent": intent,
        "tool_key": tool_key,
        "payload": payload,
        "keywords": keywords,
        "entities": entities
    }