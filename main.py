import warnings

# transformers uyarılarını bastır
warnings.filterwarnings("ignore", category=FutureWarning)
import sys
import os
import logging # <<< YENİ: Logging modülünü ekliyoruz
from response import generate_response
from memory import MemoryManager
from logger import log_event



def main():
    # Logging ayarlarını DEBUG seviyesine ayarla.
    # Bu, tüm modüllerimizdeki (retriever_stub dahil) DEBUG mesajlarının görünmesini sağlar.
    logging.basicConfig(level=logging.DEBUG, 
                        format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
    
    logger = logging.getLogger(__name__)
    
    memory = MemoryManager()
    print("Asistan aktif. 'çık' yazarak çıkabilirsiniz.\n")
    
    # Başlangıç logu
    log_event("INFO", "Asistan başlatılıyor...") 

    while True:
        try:
            user_input = input("Siz: ").strip()
            if user_input.lower() in ["çık", "exit", "quit"]:
                log_event("INFO", "Asistan kapatıldı.")
                print("Asistan: Görüşmek üzere!")
                break

            answer = generate_response(user_input)
            print("Asistan:", answer)

            # Bellek ve log kaydı
            memory.save_interaction(user_input, answer)
            log_event("INFO", f"Kullanıcı: {user_input} | Asistan: {answer}")
            
        except KeyboardInterrupt:
            log_event("INFO", "Kullanıcı tarafından durduruldu (Ctrl+C).")
            print("\nAsistan: Görüşmek üzere!")
            break
        except Exception as e:
            # Hata oluştuğunda sadece sizin özel log_event'ınız yerine, 
            # standart logging modülünü kullanarak detaylı loglama yapalım.
            logger.error(f"Beklenmedik bir hata oluştu: {e}", exc_info=True) 
            print("Asistan: Üzgünüm, beklenmedik bir hata oluştu.")


if __name__ == "__main__":
    main()