from nlu import interpret_text
from retriever import retrieve_info # Adı artık retriever.py

# MemoryManager artık main.py'de yaratılıp buraya gönderiliyor, bu yüzden burada çağırmıyoruz.

def generate_response(user_input: str, memory) -> str:
    """
    Kullanıcı girdisini analiz eder ve cevabı oluşturur.
    MemoryManager nesnesini etkileşim kaydı için kullanır.
    """
    analysis = interpret_text(user_input)
    intent = analysis["intent"]
    keywords = analysis["keywords"]

    if intent == "query":
        # NLU'dan gelen tüm keywords'leri birleştirmek yerine,
        # sadece ilk 3 anahtar kelimeyi alarak "pekala" gibi kelimeleri atlayabiliriz.
        # Bu, NLU geliştirmesi yapılana kadar geçici bir çözümdür.
        search_terms = " ".join(keywords[:3]) # İlk 3 kelimeyi al
        
        # Eğer ilk kelime "pekala" ise, sorgu boş kalır, bu yüzden bu riskli.
        # En iyisi, retriever.py'nin yaptığı gibi, yine de tüm kelimeleri göndermek.
        topic = " ".join(keywords)

        result = retrieve_info(topic)
        
        # Etkileşim kaydı
        memory.save_interaction(user_input, result)
        
        return result

    elif "merhaba" in user_input.lower():
        # Etkileşim kaydı (Query olmasa da kaydetmeliyiz)
        response_text = "Merhaba! Size nasıl yardımcı olabilirim?"
        memory.save_interaction(user_input, response_text)
        return response_text

    elif "nasılsın" in user_input.lower():
        # Etkileşim kaydı
        response_text = "İyiyim, teşekkür ederim. Siz nasılsınız?"
        memory.save_interaction(user_input, response_text)
        return response_text

    else:
        # Etkileşim kaydı
        response_text = "Bu konuda emin değilim, biraz daha detay verebilir misiniz?"
        memory.save_interaction(user_input, response_text)
        return response_text