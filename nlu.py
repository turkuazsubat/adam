import spacy
import re # Düzenli ifadeler için gerekli
nlp = spacy.load("en_core_web_sm") 

def clean_payload(text: str, triggers: list) -> str:
    text_lower = text.lower().strip()
    for trigger in triggers:
        if text_lower.endswith(trigger):
            return text[:-len(trigger)].strip()
    return text

def interpret_text(text: str):
    doc = nlp(text)
    keywords = [token.lemma_.lower() for token in doc if token.is_alpha]
    entities = [(ent.text, ent.label_) for ent in doc.ents]
    
    raw_text = text
    text_lower = text.lower().strip()
    intent = "general" 
    tool_key = None 
    payload = raw_text
    
    # --- HAFTA 12: PROFIL GÜNCELLEME YAKALAYICI (ÖNCELİKLİ) ---
    
    # 1. İsim Güncelleme (Örn: "Adım Adam", "Bana Kaptan de")
    # ([\w\s]+?) : Bu kısım ismi yakalayan 'Capture Group' (Yakalama Grubu) kısmıdır.
    name_match = re.search(r"(?:adım|ismim|bana)\s+([\w\s]+?)(?:\s+olsun|\s+de|$)", text_lower)
    if name_match:
        return {
            "intent": "profile_update",
            "key": "user_name",
            "value": name_match.group(1).strip().capitalize(),
            "keywords": keywords, "entities": entities
        }

    # 2. Üslup Güncelleme (Örn: "Üslubun sert olsun", "Tavrın ciddi olsun")
    tone_match = re.search(r"(?:üslubun|tavrın|konuşman)\s+([\w\s]+?)(?:\s+olsun|$)", text_lower)
    if tone_match:
        return {
            "intent": "profile_update",
            "key": "tone",
            "value": tone_match.group(1).strip(),
            "keywords": keywords, "entities": entities
        }

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