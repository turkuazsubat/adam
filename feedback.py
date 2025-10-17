def get_feedback():
    fb = input("Cevap tatmin edici miydi? (e/h): ").strip().lower()
    return fb == "e"
