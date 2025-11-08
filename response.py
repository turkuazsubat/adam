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

    #---- Yönlendirici (Router)-----

    #1.Niyet Komut (Hafta 6 Güncellendi)
    if intent == "command":
        
        tool_key = analysis.get("tool_key")
        payload = analysis.get("payload")

        # 'çık' komutu (main.py zaten yakalıyor ama NLU'da da var)
        if tool_key:
            # --- KRİTİK GÜNCELLEME (V2) ---
            # Artık 'find_tool_for_command' ÇAĞIRMIYORUZ.
            # Doğrudan 'execute_tool'u 'tool_key' ile çağırıyoruz.
            result = tool_manager.execute_tool(tool_key, payload)
            
            # Not: Komutların sonucunu interactions'a kaydedebiliriz (şimdilik atlıyoruz)
            # memory.save_interaction(user_input, result) 
            return result
        else:
            # Niyet "command" ama NLU uygun 'tool_key' bulamadı
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