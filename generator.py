import logging
import torch
from transformers import MBartForConditionalGeneration, MBart50TokenizerFast

# Gereksiz kütüphane gürültüsünü engellemek için logger ayarı
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

class LocalGenerator:
    """
    mBART-50 modelini kullanarak yüksek kaliteli Türkçe özetleme ve üretim yapar.
    """
    def __init__(self):
        # mBART-50 Many-to-Many model adı
        self.model_name = "facebook/mbart-large-50-many-to-many-mmt"
        
        # CPU mu GPU mu kullanılacağını belirle (Nvidia ekran kartı yoksa CPU seçer)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        self.tokenizer = None
        self.model = None
        self.load_model()

    def load_model(self):
        """Modeli ve Tokenizer'ı belleğe yükler."""
        try:
            print(f"⏳ mBART Modeli belleğe yükleniyor ({self.device})...")
            
            # Tokenizer: Metni modelin anlayacağı sayılara çeviren araçtır.
            self.tokenizer = MBart50TokenizerFast.from_pretrained(self.model_name)
            
            # Model ağırlıklarını yükle
            self.model = MBartForConditionalGeneration.from_pretrained(self.model_name).to(self.device)
            
            # Kaynak dili Türkçe (tr_TR) olarak sabitle
            self.tokenizer.src_lang = "tr_TR"
            
            print("✅ mBART başarıyla yüklendi ve göreve hazır.")
        except Exception as e:
            print(f"❌ mBART Yükleme Hatası: {e}")
            self.model = None

    def generate(self, context: str, instruction: str, max_length=200) -> str:
        """
        Gelen metni talimata göre işler.
        """
        if self.model is None:
            return "Model yüklü değil"

        try:
            # Talimat ve bağlamı birleştir
            full_prompt = f"{instruction}\nBağlam: {context}"
            
            # Metni sayılara (token) çevir
            inputs = self.tokenizer(full_prompt, return_tensors="pt", truncation=True, max_length=1024).to(self.device)
            
            # Cevap üret (Beam Search kullanarak daha mantıklı cümleler kurar)
            # Beam Search: En yüksek olasılıklı kelime gruplarını arama yöntemidir.
            summary_ids = self.model.generate(
                inputs["input_ids"],
                forced_bos_token_id=self.tokenizer.lang_code_to_id["tr_TR"], # Çıktıyı Türkçe zorla
                max_length=max_length,
                num_beams=4,
                early_stopping=True
            )
            
            
            # Sayıları tekrar metne çevir
            response = self.tokenizer.batch_decode(summary_ids, skip_special_tokens=True)[0]
            
            #Hafta 13 Çıktı Temizleme
            #Model, kendisine verilen taliamtları(user_adı, üslüo vb) cevaba dahil ederse onları ayıklar

            if "Bağlam:" in response:
                #Metni "Bağlam:" kelimesinden böler ve en son(gerçek cevap) kısmı alır.
                response = response.split("Bağlam:")[-1].strip()

            elif "User adı" in response or "Üslup" in response:
                # Eğer "Bağlam:" kelimesini yuttuysa ama talimatlar oradaysa, 
                # cümle yapısına göre ilk 2-3 talimat cümlesini atlamaya çalışır.
                parts = response.split(". ")
                if len(parts) >2:
                    response=". ".join(parts[2:]).strip()

            #Hafta 13 Çıktı Temizleme sonu

            
            return response

        except Exception as e:
            print(f"⚠️ Üretim Hatası: {e}")
            return "Metin işlenirken bir sorun oluştu."