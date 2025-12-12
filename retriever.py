import logging
import subprocess 
import json       
import urllib.parse 

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
        logger.error(f"CURL Hatası: {e}")
    return None

def clean_query_for_wikipedia(query):
    """
    Türkçe ekleri ve soru kalıplarını temizleyip 'Yalın Hal' bulmaya çalışır.
    Örn: "Türkiyenin başkenti neresidir" -> "Türkiye"
    """
    # 1. Küçük harfe çevirip kelimelere ayır
    words = query.lower().split()
    
    # 2. Soru eklerini at (neresi, kimdir, nedir...)
    stop_words = ["neresi", "neresidir", "kimdir", "nedir", "ne", "hangi", "başkenti", "merkezi"]
    cleaned_words = [w for w in words if w not in stop_words]
    
    if not cleaned_words:
        return query # Temizleyince bir şey kalmazsa orijinalini döndür
        
    # 3. İlk kelimeyi al (Genelde öznedir: "Türkiyenin...")
    subject = cleaned_words[0]
    
    # 4. Basit ek temizliği (Heuristik)
    # Wikipedia 'opensearch' zaten biraz esnektir ama biz yine de yardımcı olalım
    suffixes = ["nin", "nın", "nun", "nün", "in", "ın", "un", "ün", "'nin", "'nın"]
    for suffix in suffixes:
        if subject.endswith(suffix):
            subject = subject[:-len(suffix)] # Eki kes
            break
            
    # İlk harfi büyüt (Wikipedia başlık formatı: Türkiye)
    return subject.capitalize()

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
        return "Boş sorgu."

    # 1. HAFIZA
    try:
        if memory:
            memory_result = memory.read_from_memory(query) 
            if memory_result:
                return f"{memory_result}\n(Hafızadan)"
    except:
        pass

    # 2. İNTERNET (CURL)
    try:
        logger.info(f"İnternet Araması: {query}")
        
        # YÖNTEM A: Direkt Temizlenmiş Başlığı Dene ("Türkiye")
        # "Türkiyenin başkenti" -> "Türkiye" olarak temizlenir.
        clean_subject = clean_query_for_wikipedia(query)
        logger.info(f"Temizlenmiş Özne: {clean_subject}")
        
        # OpenSearch API: Başlık önerir (En güvenlisi budur, metin aramaz)
        # Örn: "Türkiye" yazarız -> Bize ["Türkiye", "Türkiye Cumhuriyeti"] döner.
        encoded_query = urllib.parse.quote(clean_subject)
        opensearch_url = f"https://tr.wikipedia.org/w/api.php?action=opensearch&search={encoded_query}&limit=1&namespace=0&format=json"
        
        opensearch_res = run_pure_curl(opensearch_url)
        
        best_title = None
        if opensearch_res:
            data = json.loads(opensearch_res)
            # data[1] başlıkları içerir
            if len(data) > 1 and len(data[1]) > 0:
                best_title = data[1][0]
                logger.info(f"OpenSearch Eşleşmesi: {best_title}")
        
        # Eğer OpenSearch bulduysa, onun özetini çek
        if best_title:
            summary = get_wikipedia_summary(best_title)
            if summary:
                return f"{summary}\n\n*(Kaynak: Wikipedia - {best_title})*"
        
        # YÖNTEM B: Eğer A başarısızsa, sorgunun kendisiyle dene (Fallback)
        # Belki kullanıcı "Rize Kalesi" gibi spesifik bir şey sordu ve biz temizlerken bozduk.
        if query != clean_subject:
             encoded_raw = urllib.parse.quote(query)
             opensearch_url_raw = f"https://tr.wikipedia.org/w/api.php?action=opensearch&search={encoded_raw}&limit=1&namespace=0&format=json"
             raw_res = run_pure_curl(opensearch_url_raw)
             if raw_res:
                 data = json.loads(raw_res)
                 if len(data) > 1 and len(data[1]) > 0:
                     fallback_title = data[1][0]
                     summary = get_wikipedia_summary(fallback_title)
                     if summary:
                         return f"{summary}\n\n*(Kaynak: Wikipedia - {fallback_title})*"

    except Exception as e:
        logger.error(f"İnternet hatası: {e}")

    return "İnternet bağlantısında sorun var veya Wikipedia yanıt vermiyor."