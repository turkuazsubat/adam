import os
import logging
from pathlib import Path
import subprocess 
import json       
import requests
import urllib3

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# KRİTİK DÜZELTME: Fonksiyon imzası sadeleşti (artık sadece HAM query alıyor)
def retrieve_info(query: str, memory) -> str:
    """
    Bilgi alma fonksiyonu:
    1. Önce kalıcı hafızaya (query [ham girdi] ile) bakar.
    2. Bulamazsa Curl ile API'den (query'yi işleyerek) sorgu çeker.
    3. Bulamazsa yerel dosyalardan (query'yi işleyerek) okur.
    """
    query = query.strip() # Gelen ham girdiyi temizle
    if not query:
        logger.warning("Boş sorgu alındı.")
        return "Boş bir sorgu girdiniz. Lütfen geçerli bir kelime veya konu yazın."

    # -------------------------------
    # 1️⃣ KALICI HAFIZADAN OKUMA (raw_query kullanılır)
    # -------------------------------
    try:
        # memory.read_from_memory, ham 'query'yi alır ve 'normalize_query' ile temizler
        memory_result = memory.read_from_memory(query) 
        if memory_result:
            logger.info("Cevap, kalıcı hafızadan çekildi (Öğrenilmiş bilgi).")
            # Cevabı hemen buradan döndür
            return f"{memory_result}\nBu bilgi asistanın öğrendiği kalıcı hafızadan çekilmiştir."
            
    except Exception as e:
        logger.error(f"Kalıcı hafızadan okuma hatası: {e}")

    # -------------------------------
    # 2️⃣ ÇEVRİMİÇİ SORGULAMA (API)
    # -------------------------------
    
    # API için 'topic'i BURADA, ham 'query'den üret.
    topic_for_api = query.split()[0].lower() 
    
    extract = None
    try:
        topic_encoded = topic_for_api.replace(' ', '_') 
        url = f"https://tr.wikipedia.org/api/rest_v1/page/summary/{topic_encoded}"
        
        curl_command = ["curl", "-s", "-k", "-L", url]
        logger.info(f"Curl API isteği başlatılıyor: {url}")
        
        result = subprocess.run(
            curl_command, 
            capture_output=True, 
            text=True, 
            encoding='utf-8', 
            check=False, 
            timeout=15
        )
        if result.returncode == 0:
            try:
                data = json.loads(result.stdout)
                extract = data.get("extract") 
                
                if extract:
                    logger.info("Curl ile API'den bilgi başarıyla alındı.")
                    return extract
                else:
                    logger.warning("API yanıtı geçerli ancak 'extract' alanı boş (404/Bulunamadı).")
            except json.JSONDecodeError:
                logger.error("Curl çıktısı geçerli JSON değil. Sunucu veya ağ hatası olabilir.")
        else:
            logger.error(f"Curl komutu hata kodu döndürdü ({result.returncode}): {result.stderr.strip()}")
            
    except Exception as e:
        logger.error(f"Genel Curl çalıştırma hatası: {e}")

    # -------------------------------
    # 3️⃣ YEREL YEDEKLEME (topic kullanılır)
    # -------------------------------
    local_dir = Path("data/sample_docs")
    keyword = topic_for_api 
    best_match = None

    for file in local_dir.glob("*.txt"):
        if keyword in file.stem.lower(): 
            best_match = file
            break

    if best_match:
        try:
            with open(best_match, "r", encoding="utf-8") as f:
                content = f.read().strip()
                logger.info(f"Yerel dosyadan bilgi çekildi: {best_match.name}")
                return f"{content}\nBu bilgi yerel dosyalardan çekilmiştir."
        except Exception as e:
            logger.error(f"Yerel dosya okuma hatası: {best_match.name} | {e}")
    else:
        logger.warning(f"Eşleşen yerel dosya bulunamadı (sorgu: {keyword}).")

    # -------------------------------
    # 4️⃣ Hiçbir şey bulunamazsa
    # -------------------------------
    return "Bilgiye ulaşılamadı. Yardımcı olabileceğim başka bir konu var mı?"