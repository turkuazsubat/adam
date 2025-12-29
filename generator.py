import logging
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch

#Loglama yapılandırması
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class LocalGenerator:
    """
    Google Flan-T5 modelini kullanarak yerel metin üretimi ve işleme yapar.
    """

    def __init__(self):
        #Başlangıç modeli: google/flan-t5-base
        self.model_name = "google/flan-t5-base"
        self.device = "cpu"  # GPU varsa "cuda" yapılabilir, kararlılık için cpu seçildi
        self.tokenizer = None
        self.model = None

        self.load_model()

    def load_model(self):
        '''Modeli ve Tokenizer'ı belleğe yükler.'''
        try:
            print(f"Model yükleniyor: {self.model_name}")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name).to(self.device)
            print("Model başarıyla yüklendi.")
        except Exception as e:
            logger.error(f"Model yükleme hatası: {e}")
            self.model = None

    def generate(self,context:str,instruction:str,max_length=200,min_length=0) -> str:
        '''
        Verilen bağlam(context) ve talimata(instruction) göre cevap üretir.
        min_length varsayılan olarak 0 yapıldı.
        Kısa cevap gerektiren sorularda modelin saçmalamasını engeller.
        '''

        if not self.model:
            return "Model yüklü değil"
        
        try:
            #t5 prompt formatı: "Instruction: <talimat> Context: <metin>"
            input_text = f"{instruction}\n\nContext: {context}"

            #Girdiyi vektöre çevir
            inputs = self.tokenizer(input_text,return_tensors="pt", max_length=512, truncation=True).to(self.device)

            #Çıktı üretimi
            outputs = self.model.generate(
                inputs.input_ids,
                max_length=max_length,
                min_length=min_length, #Dinamik uzunluk
                num_beams= 4, #Daha kaliteli cümleler için beam search
                early_stopping=True,
                length_penalty=1.0 #2 idi normalize edildi
            )

            #Vektörü metne çevir
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            return response
           
        except Exception as e:
            logger.error(f"Üretim hatası: {e}")
            return "Hata oluştu."
        
#Modül Testi
if __name__ == "__main__":
    print("GENERATOR MODÜL TESTİ")
    gen=LocalGenerator()


    if gen.model:
        # Örnek Senaryo: Wikipedia'dan gelen ham metin
        test_context = (
            "Türkiye, başkenti Ankara olan ve hem Asya hem Avrupa'da toprağı bulunan bir ülkedir. "
            "Nüfusu 85 milyon civarındadır. Yönetim şekli Cumhuriyettir."
        )
        
        # Test 1: Kısa Cevap (min_length=1 veriyoruz ki uzatmasın)
        print("\n[TEST 1] Soru Cevaplama (Kısa):")
        q1 = "What is the capital of Turkey?"
        # Instruction'ı netleştiriyoruz
        res1 = gen.generate(test_context, f"Answer the question based on context: {q1}", min_length=1)
        print(f"Soru: {q1}\nCevap: {res1}")

        # Test 2: Özetleme (min_length=10 veriyoruz ki cümle kursun)
        print("\n[TEST 2] Özetleme (Uzun):")
        q2 = "Summarize the text."
        res2 = gen.generate(test_context, q2, min_length=15)
        print(f"Komut: {q2}\nCevap: {res2}")