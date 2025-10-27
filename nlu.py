import spacy
nlp = spacy.load("en_core_web_sm") 

def interpret_text(text: str):
    doc = nlp(text)
    
    keywords = [token.lemma_.lower() for token in doc if token.is_alpha]
    entities = [(ent.text, ent.label_) for ent in doc.ents]
    
    # 3. Amaç (Intent) Düzeltmesi (DAHA KAPSAYICI YENİ MANTIK):
    # Eğer metin 'nedir', 'ara', 'bilgi', '?' içeriyorsa VEYA 
    # 5 kelimeden uzunsa (uzunluk bazlı sezgisel tahmin)
    if ("nedir" in text.lower() or 
        "ara" in text.lower() or 
        "bilgi" in text.lower() or 
        "bahseder" in text.lower() or # "bahseder misin" gibi ifadeleri de yakala
        "?" in text or 
        len(text.split()) >= 5): # <<< YENİ: Uzun sorguları 'query' kabul et
        intent = "query"
    else:
        # Tekrar kontrol: Sadece 'çık' yazılmışsa 'command' yap (ileri aşama için)
        if text.lower() in ["çık", "exit", "quit"]:
             intent = "command"
        else:
             intent = "general" 
    
    return {
        "intent": intent,
        "keywords": keywords,
        "entities": entities
    }