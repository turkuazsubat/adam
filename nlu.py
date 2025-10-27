import spacy

# Spacy modelinizi yüklüyoruz. Eğer farklı bir dil modeli kullanıyorsanız, burayı değiştirin.
# Önceden karşılaştığınız spacy/numpy sorunlarını çözdükten sonra bu satır artık çalışmalı.
nlp = spacy.load("en_core_web_sm") 

def interpret_text(text: str):
    """
    Kullanıcı metnini analiz eder ve amaç (intent) ile anahtar kelimeleri çıkarır.
    """
    doc = nlp(text)
    
    # 1. Anahtar Kelimeler (Keywords): 
    # Sadece alfabetik kelimeleri kök (lemma) haline getirerek çıkarırız.
    keywords = [token.lemma_.lower() for token in doc if token.is_alpha]
    
    # 2. Varlıklar (Entities) (Şimdilik sadece çıkarılıyor, kullanılmayabilir)
    entities = [(ent.text, ent.label_) for ent in doc.ents]
    
    # 3. Amaç (Intent) Düzeltmesi: 
    # 'nedir', 'ara', 'bilgi' kelimeleri veya '?' işareti varsa, sorgu (query) kabul et.
    # Bu, 'Roma tarihi hakkında bilgi verir misin' sorgusunun 'query' olmasını sağlar.
    if "nedir" in text.lower() or "ara" in text.lower() or "bilgi" in text.lower() or "?" in text:
        intent = "query"
    else:
        intent = "general" # Merhaba, nasılsın, çık gibi genel komutlar.
    
    # Not: Response modülü sadece 'query' intent'i için bilgi çekmeyi dener.
    
    return {
        "intent": intent,
        "keywords": keywords,
        "entities": entities
    }
