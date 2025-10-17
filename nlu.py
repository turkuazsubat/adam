import spacy
nlp = spacy.load("en_core_web_sm")

def interpret_text(text):
    doc = nlp(text.lower())
    if "aç" in text and "hesap" in text:
        return "open_calculator"
    if "not" in text or "kaydet" in text:
        return "take_note"
    return "general_query"
