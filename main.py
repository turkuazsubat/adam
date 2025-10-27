import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
import sys
import os
import logging
from response import generate_response
from memory import MemoryManager 
from logger import log_event # <<< logger.py'den alıyoruz

# Veritabanı ve şema dosya yolları
DB_PATH = "db/project.db" # db klasörü içine
SCHEMA_PATH = "db_schema.sql" # Ana dizinde

# Artık main.py'de log_event'i import ettiğimiz için, MemoryManager'ı doğru yollarla başlatabiliriz.

def main():
    logging.basicConfig(
        level=logging.DEBUG, # Geliştirme aşamasında hala DEBUG seviyesini koruyalım
        format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
        filename='project.log', # Tüm logları bu dosyaya yaz
        filemode='a' # Dosyanın sonuna ekle (overwrite yapma)
    )

    logger = logging.getLogger(__name__)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.ERROR)
    logger = logging.getLogger(__name__)
    
    # YENİ HAFıZA BAŞLATMA: Veritabanı ve şema yollarını geçiriyoruz.
    # Bu, ilk çalıştırmada db/project.db dosyasını oluşturur ve tabloları kurar.
    try:
        memory = MemoryManager(db_path=DB_PATH, schema_path=SCHEMA_PATH) 
    except Exception as e:
        log_event("CRITICAL", f"Hafıza Yöneticisi başlatılamadı: {e}")
        # Programı kapatmak isteyebilirsiniz, şimdilik devam edelim.
        print("Hata: Veritabanı başlatılamadığı için asistan düzgün çalışmayabilir.")
        return # Başlatma başarısızsa çıkış yap.
    
    print("Asistan aktif. 'çık' yazarak çıkabilirsiniz.\n")
    log_event("INFO", "Asistan başlatılıyor...") 

    while True:
        try:
            user_input = input("Siz: ").strip()
            if user_input.lower() in ["çık", "exit", "quit"]:
                log_event("INFO", "Asistan kapatıldı.")
                # Bağlantıyı kapatmayı unutmayalım
                memory.close() 
                print("Asistan: Görüşmek üzere!")
                break

            answer = generate_response(user_input, memory) # <<< memory'yi de gönderiyoruz
            print("Asistan:", answer)

            # memory.save_interaction çağrısı zaten response.py'de yapılıyor.
            log_event("INFO", f"Kullanıcı: {user_input} | Asistan: {answer}")
            
        except KeyboardInterrupt:
            log_event("INFO", "Kullanıcı tarafından durduruldu (Ctrl+C).")
            memory.close() 
            print("\nAsistan: Görüşmek üzere!")
            break
        except Exception as e:
            logger.error(f"Beklenmedik bir hata oluştu: {e}", exc_info=True) 
            print("Asistan: Üzgünüm, beklenmedik bir hata oluştu.")


if __name__ == "__main__":
    main()