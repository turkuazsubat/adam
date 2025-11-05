from nlu import interpret_text
from retriever import retrieve_info # Adı artık retriever.py

# MemoryManager artık main.py'de yaratılıp buraya gönderiliyor, bu yüzden burada çağırmıyoruz.

def generate_response(user_input: str, memory,tool_manager) -> str: #Hafta5: tool_manager
    """
    Kullanıcı girdisini analiz eder ve cevabı oluşturur.
    MemoryManager nesnesini etkileşim kaydı için kullanır.
    """
    analysis = interpret_text(user_input)
    intent = analysis["intent"]
    
    keywords = analysis.get("keywords",[])
    raw_text = analysis.get("raw_text", user_input)

    #1.Niyet Komut (Hafta 5)
    if intent == "command":
        
        
        # Hangi aracın çalışacağını bul
        tool_name = tool_manager.find_tool_for_command(keywords)
        
        if tool_name:
            # KRİTİK DÜZELTME: Aracın adını değil, aracın sonucunu döndür.
            # tool_manager'a aracı çalıştırmasını söylüyoruz (execute_tool).
            result = tool_manager.execute_tool(tool_name, raw_text)
            return result
        else:
            # Niyet "command" ama uygun araç bulunamadı
            response_text = "Komutunuzu anladım ancak bu eylemi gerçekleştirecek uygun bir araç bulamadım."
            memory.save_interaction(user_input, response_text)
            return response_text
    #2. Niyet: Sorgulama(Hafta3-4)

    elif intent == "query":
        # Hafıza araması ve API araması için retriever'a ham girdiyi (user_input) gönderiyoruz
        # (Bu, Hafta 4'te yaptığımız son düzeltmeydi ve doğruydu)
        result = retrieve_info(user_input, memory) 
        
        # Etkileşim kaydı
        memory.save_interaction(user_input, result)
        
        return result

    #3. Niyet: Genel (Hafta 1-2)
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