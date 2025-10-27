from nlu import interpret_text
from retriever_stub import retrieve_info
from memory import MemoryManager

memory = MemoryManager()

def generate_response(user_input: str) -> str:
    analysis = interpret_text(user_input)
    intent = analysis["intent"]
    keywords = analysis["keywords"]

    if intent == "query":
        topic = " ".join(keywords)
        result = retrieve_info(topic)
        memory.save_interaction(user_input, result)
        return result

    elif "merhaba" in user_input.lower():
        return "Merhaba! Size nasıl yardımcı olabilirim?"

    elif "nasılsın" in user_input.lower():
        return "İyiyim, teşekkür ederim. Siz nasılsınız?"

    else:
        return "Bu konuda emin değilim, biraz daha detay verebilir misiniz?"

