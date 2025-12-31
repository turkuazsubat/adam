import logging
import subprocess 
import json       
import urllib.parse 
import re # HAFTA 13: Regex işlemleri için eklendi

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def run_pure_curl(url):
    """
    Python kütüphanesi kullanmadan, Windows'un curl.exe'si ile veri çeker.
    SSL hatalarını (-k) ve Yönlendirmeleri (-L) otomatik halleder.
    """
    try:
        # -k: Insecure (SSL Yoksay)
        # -s: Silent (Gereksiz çıktı verme)
        # -L: Redirectleri takip et
        # -A: User-Agent (Wikipedia bot sanmasın)
        command = ['curl', '-k', '-s', '-L', '-A', 'Mozilla/5.0', url]
        
        # subprocess.CREATE_NO_WINDOW: Siyah ekran açılıp kapanmasın
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding='utf-8',
            creationflags=subprocess.CREATE_NO_WINDOW 
        )
        
        if result.returncode == 0:
            return result.stdout
    except Exception as e:
        logger.error(f"CURL Hatasi: {e}")
    return None

def clean_query_for_wikipedia(query):
    """
    Türkçe ekleri ve soru kalıplarını temizleyip 'Yalın Hal' bulmaya çalışır.
    Örn: "Türkiyenin başkenti neresidir" -> "Türkiye"
    """

    # --- HAFTA 13 DÜZELTME: Noktalama işaretlerini temizle ---
    # Sorgunun sonundaki ? ! . gibi işaretleri kaldırıyoruz.
    query = re.sub(r'[^\w\s]', '', query)

    # 1. Küçük harfe çevirip kelimelere ayır
    words = query.lower().split()
    
    # Hafta 13 güncellemesi: genişletilmiş stopwords
    # hem.. hem... hatasını önlemek için bağlaçlar eklendi
    # 2. Soru eklerini at (neresi, kimdir, nedir...)
    stop_words = [
        "hem", "ve", "ile", "de", "da", "bir", "nedir", "nelerdir", "hakkında",
        "neresi", "neresidir", "kimdir", "ne", "hangi", "başkenti", "merkezi",
        "nerede", "nasıl", "yer", "yetişir", "olur", "istiyorum", "bilgi", "ver"
    ]
    cleaned_words = [w for w in words if w not in stop_words]
    
    if not cleaned_words:
        return query # Temizleyince bir şey kalmazsa orijinalini döndür
        
    # 3. İlk kelimeyi al (Genelde öznedir: "Türkiyenin...")
    # Hafta 13 notu: sadece ilk kelimeyi değil, anlamlı tüm kelimeleri birleştirir
    # örn: mersin ve istanbul" -> "Mersin istanbul"
    subject = " ".join(cleaned_words)
    
    # ilk kelime üzerinden ek temizliği (Heuristik korundu)
    first_word = cleaned_words[0]
    
    # 4. Basit ek temizliği (Heuristik)
    # Wikipedia 'opensearch' zaten biraz esnektir ama biz yine de yardımcı olalım
    suffixes = ["nin", "nın", "nun", "nün", "in", "ın", "un", "ün", "'nin", "'nın"]
    for suffix in suffixes:
        if first_word.endswith(suffix):
            first_word = first_word[:-len(suffix)] # Eki kes
            break
            
    # temizlenmiş ilk kelimeyi ve geri kalanları birleştir (wikipedia için optimize)
    final_subject = first_word.capitalize()
    if len(cleaned_words) > 1:
        final_subject = first_word.capitalize() + " " + " ".join(cleaned_words[1:])

    # İlk harfi büyüt (Wikipedia başlık formatı: Türkiye)
    return final_subject

def get_wikipedia_summary(title):
    """
    Verilen NET BAŞLIĞIN özetini çeker.
    """
    try:
        encoded_title = urllib.parse.quote(title)
        url = f"https://tr.wikipedia.org/api/rest_v1/page/summary/{encoded_title}"
        
        json_response = run_pure_curl(url)
        if json_response:
            data = json.loads(json_response)
            
            # Eğer "Anlam Ayrımı" sayfasıysa (Örn: Rize (İl) vs Rize (Şehir))
            if data.get("type") == "disambiguation":
                return None # Net bir cevap değil, aramaya devam etmeli
            
            return data.get("extract")
    except:
        pass
    return None

def retrieve_info(query: str, memory) -> str:
    """
    Ana Fonksiyon:
    1. Hafıza kontrolü.
    2. CURL + OpenSearch (Başlık Tamamlama).
    3. CURL + Summary (Özet Çekme).
    """
    query = query.strip()
    if not query:
        return "Bos sorgu."

    # 1. HAFIZA
    try:
        if memory:
            memory_result = memory.read_from_memory(query) 
            if memory_result:
                return f"{memory_result}\n(Hafizadan)"
    except:
        pass

    # 2. İNTERNET (CURL)
    try:
        logger.info(f"Internet Aramasi: {query}")
        
        # Hafta 13: Sorgulama Öncesi Temizlik
        clean_subject = clean_query_for_wikipedia(query)
        logger.info(f"Temizlenmis Ozne: {clean_subject}")
        
        # OpenSearch API: Başlık önerir
        encoded_query = urllib.parse.quote(clean_subject)
        opensearch_url = f"https://tr.wikipedia.org/w/api.php?action=opensearch&search={encoded_query}&limit=1&namespace=0&format=json"
        
        opensearch_res = run_pure_curl(opensearch_url)
        
        best_title = None
        if opensearch_res:
            data = json.loads(opensearch_res)
            if len(data) > 1 and len(data[1]) > 0:
                best_title = data[1][0]
                logger.info(f"OpenSearch Eslesmesi: {best_title}")
        
        # Eğer OpenSearch bulduysa, onun özetini çek
        if best_title:
            summary = get_wikipedia_summary(best_title)
            if summary:
                return f"{summary}\n\n*(Kaynak: Wikipedia - {best_title})*"
        
        # --- HAFTA 13: SON SANS (LAST RESORT) STRATEJISI ---
        # Eger uzun temiz sorgu sonuc vermediyse, cumlenin sonundaki temel kelimeyi dene.
        # --- HAFTA 13: AKILLI SON ŞANS ---
        words = clean_subject.split()
        if words:
            # 'nedir', 'cismi', 'adı' gibi kelimeleri atla, bir öncekini özne seç
            last_resort_term = words[-1]
            stop_terms = ["nedir", "ne", "adı", "cismi", "olan", "seydir", "denir"]
            if last_resort_term in stop_terms and len(words) > 1:
                last_resort_term = words[-2]
            
            logger.info(f"Son şans araması: {last_resort_term}")
            # Wikipedia araması devam eder...
            encoded_last = urllib.parse.quote(last_resort_term)
            url_last = f"https://tr.wikipedia.org/w/api.php?action=opensearch&search={encoded_last}&limit=1&namespace=0&format=json"
            res_last = run_pure_curl(url_last)
            
            if res_last:
                data_last = json.loads(res_last)
                if len(data_last) > 1 and len(data_last[1]) > 0:
                    best_title = data_last[1][0]
                    summary = get_wikipedia_summary(best_title)
                    if summary:
                        return f"Net bir eslesme bulamadim ama sunu buldum:\n\n{summary}\n\n*(Kaynak: Wikipedia - {best_title})*"

        return f"Uzgunum Yavuz, '{query}' hakkinda Wikipedia'da bir baslik bulamadim."

    except Exception as e:
        logger.error(f"Internet hatasi: {e}")

    return f"Uzgunum Yavuz, '{query}' hakkinda Wikipedia'da bir baslik bulamadim."