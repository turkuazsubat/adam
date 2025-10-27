# retriever_stub.py
import requests
import os
import logging
from pathlib import Path
import urllib3

# -------------------------------
# Log ayarları
# -------------------------------
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# -------------------------------
# Güvenli olmayan SSL uyarılarını kapat
# -------------------------------
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def retrieve_info(query: str) -> str:
    """
    Bilgi alma fonksiyonu:
    1. Önce Wikipedia API'sinden sorgu çeker.
    2. Başarısız olursa 'data/sample_docs' altındaki yerel dosyalardan okur.
    """
    query = query.strip()
    if not query:
        logger.warning("Boş sorgu alındı.")
        return "Boş bir sorgu girdiniz. Lütfen geçerli bir kelime veya konu yazın."

    # -------------------------------
    # 1️⃣ ÇEVRİMİÇİ SORGULAMA (Wikipedia REST API)
    # -------------------------------
    try:
        url = f"https://tr.wikipedia.org/api/rest_v1/page/summary/{query.replace(' ', '_')}"
        logger.info(f"Wikipedia API isteği: {url}")
        response = requests.get(url, timeout=10, verify=False)  # SSL doğrulama devre dışı

        if response.status_code == 200:
            data = response.json()
            extract = data.get("extract")
            if extract:
                logger.info("API'den bilgi başarıyla alındı.")
                return extract
            else:
                logger.warning("API yanıtı geçerli ancak 'extract' alanı boş.")
        elif response.status_code == 404:
            logger.warning(f"API: '{query}' konusu bulunamadı (404).")
        else:
            logger.warning(f"API beklenmedik durum kodu döndürdü: {response.status_code}")

    except requests.exceptions.RequestException as e:
        logger.error(f"API isteği başarısız ({type(e).__name__}): {e}")

    # -------------------------------
    # 2️⃣ YEREL YEDEKLEME (Fallback)
    # -------------------------------
    local_dir = Path("data/sample_docs")
    if not local_dir.exists():
        logger.error(f"Yerel veri klasörü bulunamadı: {local_dir}")
        return "Bilgiye ulaşılamadı (yerel veri klasörü mevcut değil)."

    # Arama kelimesini sadeleştir
    keyword = query.split()[0].lower()
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
                return content if content else "Yerel dosya boş görünüyor."
        except Exception as e:
            logger.error(f"Yerel dosya okuma hatası: {best_match.name} | {e}")
    else:
        logger.warning(f"Eşleşen yerel dosya bulunamadı (sorgu: {keyword}).")

    # -------------------------------
    # 3️⃣ Hiçbir şey bulunamazsa
    # -------------------------------
    return "Bilgiye ulaşılamadı. Yardımcı olabileceğim başka bir konu var mı?"
