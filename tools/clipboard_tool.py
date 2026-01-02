import pyperclip

def read_clipboard(dummy_arg=None):
    '''
    Sistem panosundaki (Clipboard) metni okur.
    dummy_arg: ToolManager yapısı gereği bazen boş argüman gelebilir, onu yutmak için 
    '''

    try:
        text = pyperclip.paste()

        if not text or text.strip == "":
            return "Panı şu an boş veya metin içermiyor"
        
        #Çok uzun metinlerini kırpalım mı? Şimdilik hayır, mBart halleder.
        #Sadece bilgi verelim

        word_count =len(text.split())
        return f"[PANO OKUNDU - {word_count} Kelime]:\n{text}"
    
    except Exception as e:
        return f"Pano okunurken hata oluştu: {e}"
    