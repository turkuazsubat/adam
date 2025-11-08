import os
import datetime
import logging

logger = logging.getLogger(__name__)

#Yapılacaklar listesinin kaydedileceği dosyanın yolu
TODO_FILE_PATH = "data/todo.txt"

def add_todo(item:str) -> str:

    '''
    Kullanıcıdan gelen metni (NLU'dan gelen payload) 'data/todo.txt" dosyasına kaydeder.
    Bu fonksiyon, 'görev ekle' komutuyla tetiklenir
    '''

    try:
        #Not: Payload'un 'görev ekle' gibi komut kelimeleri hala nasıl içerdiğini varsayıyoruz.
        #İleride NLU'da bu kelimeleri temizleyeceğiz. Şimdilik gam metni kaydediyoruz.

        #Dosyanın bulunduğu 'data' klasörünün var olduğundan emin ol
        os.makedirs(os.path.dirname(TODO_FILE_PATH), exist_ok=True)

        #Dosyaya ekleme moduna ('a') yaz
        with open(TODO_FILE_PATH, "a", encoding="utf-8") as f:
            f.write(f"- {item}\n") #Başına "-" koyarak lise öğesi yapalım

        logger.info(f"Yeni görev eklendi: {item}")
        return f"Şu görev eklendi: '{item}'"
    
    except Exception as e:
        logger.error(f"Görev ekleme hatası: {e}")
        return "Üzgünüm, görevinizi eklerken bir hata oluştu."
    

def list_todos() -> str:
    '''
    'data/todo.txt' dosyasındaki tüm görevleri okur ve listeler
    Bu fonksiyon, 'görev listele' komutuyla tetiklenir.
    '''

    try:
        #Dosya henüz oluşturulmamışsa
        if not os.path.exists(TODO_FILE_PATH):
            return "Yapılacaklar listeniz henüz boş."
        
        with open(TODO_FILE_PATH, "r", encoding="utf-8") as f:
            todos = f.readlines()

        if not todos:
            return "Yapıalcaklar listeniz boş"
        
        #Cevabı formatla

        response = "İşte yapılacaklar listeniz :\n"

        for i, todo in enumerate(todos,1):
            response += f"{i}. {todo.strip()}\n" #Baştaki '-' ve sondaki '\n' yi temizle

        return response
    
    except Exception as e:
        logger.error(f"Görev listeleme hatası: {e}")
        return "Üzgünüm, görevlerinizi listelerken bir hata oluştu."
    
    
