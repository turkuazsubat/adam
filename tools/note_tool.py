import os
import datetime
import logging

logger = logging.getLogger(__name__)

#Notların kaydedildiği yer
NOTES_FILE_PATH = "data/notes.txt"


def take_note(text_to_save: str) -> str:
    '''
    Kullanıcıdan gelen metni 'data/notes.txt' dosyasına zaman damgasıyla kaydeder
    '''

    try:

        #Zaman damgası
        timestamp=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        #Kaydedilecek tam metin
        note_entry = f"[{timestamp}] - {text_to_save}\n"

        #'data' klasörünü var olduğundan emin ol
        os.makedirs(os.path.dirname(NOTES_FILE_PATH), exist_ok =True)

        #Dosyaya ekleme moduna ('a') yaz

        with open(NOTES_FILE_PATH, "a", encoding="utf-8") as f:
            f.write(note_entry)

        
        logger.info(f"Not Başarıyla kaydedildi: {NOTES_FILE_PATH}")
        return "Notunuz başarıyla kaydedildi."
    
    except Exception as e:
        logger.error(f"Not Kaydetme hatası: {e}")
        return "Üzgünüm, not kaydederken bir hata oluştu."