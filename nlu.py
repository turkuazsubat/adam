import spacy
nlp = spacy.load("en_core_web_sm") 

def interpret_text(text: str):
    doc = nlp(text)
    
    keywords = [token.lemma_.lower() for token in doc if token.is_alpha]
    entities = [(ent.text, ent.label_) for ent in doc.ents]
    
    #Hafta 6 eklemeler
    raw_text = text
    intent = "general" #varsayılan text w6
    tool_key = None #Varsayılan araç
    payload = raw_text
    
    
    #Hafta 6: Niyet tanıma V2 öncelik sırasına göre 

    #1. Geri bildirim kontrolü
    if raw_text.startswith("!"):
        intent = 'feedback'

    #2. Komut(Command) Niyeti Kontrolü
    elif "not" in keywords and "al" in keywords:
        intent = "command"
        tool_key = "note"
        #Not al komutunda, komut kelimelerini ("Not al") temizleyerek payload oluşturabiliriz
        #Şimdilik basit tutalım ve ham metni gönderelim:
        payload = raw_text

    elif("görev" in keywords and "ekle" in keywords) or \
        ("yapılacak" in keywords and "ekle" in keywords):
        intent = "command"
        tool_key = "todo_add"
        #Payload'dan komut kelimelerini çıkarmak iyi bir pratik olurdu, şimdilik ham metin:
        payload= raw_text

    # --- KRİTİK DÜZELTME (Hata 1) ---
    # "listele" veya "liste" kelimelerini (ve eklerini "listem" gibi) ara
    elif ("görev" in keywords or "yapılacak" in keywords) and \
         any(k.startswith("liste") for k in keywords): # "liste", "listele", "listem" vb.
        intent = "command"
        tool_key = "todo_list"
        payload = None # Liste isterken ek yüke gerek yok
    

    elif("görev" in keywords and "liste" in keywords) or \
        ("görev" in keywords and "listele" in keywords) or \
        ("yapılacak" in keywords and "liste" in keywords):
        intent = "command"
        tool_key = "todo_list"
        payload = None #Liste isterken ek yüke gerek yok

    elif raw_text.lower() in ["çık","exit","quit"]:
        intent ="command"
        tool_key = "exit" #Özel çıkış komutu

    #3.Sorgu(Query) niyeti Hafta 3 te yapılmıştı
    elif ("nedir" in text.lower() or 
        "ara" in text.lower() or 
        "bilgi" in text.lower() or 
        "bahseder" in text.lower() or # "bahseder misin" gibi ifadeleri de yakala
        "?" in text or 
        len(text.split()) >= 3): # <<< YENİ: Uzun sorguları 'query' kabul et
        intent = "query"
    
    #4. Genel Kontrolü
    #(Yukarıdakilerin hiçbiri eşleşmezse "general" olarak kalır)

    
    return {
        "intent": intent,
        "tool_key": tool_key, #W6, Hangi aracın çalışacağını belitir
        "payload": payload, #W6, araca gönderilecek veri
        "keywords": keywords, # (Hala debug için tutuluyor)
        "entities": entities
    }