def generate_response(intent, memory):
    if intent == "open_calculator":
        return "Hesap makinesini açıyorum."
    elif intent == "take_note":
        return "Notunuzu kaydedebilirim."
    else:
        last = memory.get_last_user_input()
        return f"Bunu tam anlayamadım ama son sorduğunuz '{last}' ile ilgili olabilir."
