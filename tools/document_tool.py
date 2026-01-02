import os
import PyPDF2

#Varsayılan döküman klasörü
DOCS_DIR = os.path.join("data","sample_docs")

def read_pdf(filename:str):
    '''
    data/sample_docs altındaki bir PDF dosyasını okur.
    Sadece ilk 3 sayfayı çeker (LLM limitini aşmamak için)
    '''

    #Dosya uzantısı yokse ekle
    if not filename.endswith(".pdf"):
        filename += ".pdf"

    target_path = os.path.join(DOCS_DIR,filename)
    
    try:
        if not os.path.exists(target_path):
            return f"Hata: Dosya bulunamadı. Lütfen dosyanın '{DOCS_DIR}' içinde olduğundan emin ol. (Aranan: {filename})"
        
        text_content = ""
        
        with open(target_path,"rb") as f:
            reader = PyPDF2.PdfReader(f)
            num_pages = len(reader.pages)

            #Limit: en fazla ilk 3 sayfa veya tamamı
            read_limit = min(3,num_pages)

            for i in range(read_limit):
                page = reader.pages[i]
                text_content += page.extract_text() + "\n"
        
        if not text_content.strip():
            return f"Dosya okundu ama metin içerği boş (Görsel bazlı PDF olabilir): {filename}"
        
        return f"[PDF OKUNDU - {filename} | İlk {read_limit}/{num_pages} Sayfa]:\n{text_content}"
    
    except Exception as e:
        return f"PDF okuma hatası: {e}"