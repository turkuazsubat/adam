from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import logging
from logger import log_event

class SemanticEngine:
    # --- GÜNCELLEME: Türkçe destekleyen Multilingual Model ---
    def __init__(self, model_name='paraphrase-multilingual-MiniLM-L12-v2'):
        """
        Yerel Semantik Arama Motoru.
        Multilingual model (Türkçe dahil 50+ dil destekler).
        """
        self.model_name = model_name
        self.model = None
        self.initialize_model()

    def initialize_model(self):
        try:
            print(f"🧠 Yapay Zeka Modeli Yükleniyor: {self.model_name}")
            # Model zaten cache'de olduğu için hızlıca yüklenecek
            self.model = SentenceTransformer(self.model_name)
            log_event("INFO", f"Semantik Model Yüklendi: {self.model_name}", "semantic_engine")
            print("✅ Model Hazır ve Çalışıyor.")
        except Exception as e:
            log_event("CRITICAL", f"MODEL YÜKLEME BAŞARISIZ: {e}", "semantic_engine")
            print(f"❌ HATA: {e}")

    def encode(self, text):
        """Metni vektöre (sayı dizisine) çevirir."""
        if self.model is None:
            return None 
        return self.model.encode(text)

    def find_best_match(self, query, corpus_list, min_score=0.3):
        """
        Sorguyu (query) alır ve listedeki en alakalı metni bulur.
        """
        if not corpus_list:
            return None, 0.0

        # 1. Sorguyu vektöre çevir
        query_vec = self.encode(query)
        if query_vec is None: return None, 0.0

        # 2. Listedeki metinleri vektöre çevir
        corpus_vecs = self.model.encode(corpus_list)
        
        # 3. Benzerlikleri hesapla (Cosine Similarity)
        similarities = cosine_similarity(query_vec.reshape(1, -1), corpus_vecs)[0]
        
        # 4. En yüksek skoru bul
        best_idx = np.argmax(similarities)
        best_score = similarities[best_idx]
        
        # Eşik değer kontrolü (Alakasız şeyleri elemek için)
        if best_score < min_score:
            return "Benzer bir bilgi bulunamadı.", float(best_score)
            
        return corpus_list[best_idx], float(best_score)


# --- FİNAL TEST BLOĞU (GÜNCELLENDİ) ---
if __name__ == "__main__":
    engine = SemanticEngine()
    
    database = [
        "Türkiye'nin en kalabalık şehri İstanbul'dur.",
        "İtalya'nın başkenti Roma'dır.",
        "Bilgisayar Mühendisliği zor bir bölümdür.",
        "Karpuz yaz meyvesidir."
    ]
    
    print("\n--- TEST BAŞLIYOR ---")

    # TEST 1: Kelime farklı, Anlam aynı
    # Veritabanında "kalabalık şehir" yazıyor, biz "nüfusu yoğun il" diyeceğiz.
    # Keyword search (Ctrl+F) bunu bulamazdı, ama Semantic Search bulmalı.
    sorgu1 = "Türkiye'nin nüfusu en yoğun ili hangisidir?"
    
    print(f"\nSoru 1: {sorgu1}")
    cevap, skor = engine.find_best_match(sorgu1, database, min_score=0.25) # Eşiği biraz düşürdük
    print(f"Cevap: {cevap}")
    print(f"Skor: {skor:.4f}")
    
    # TEST 2: İtalya Örneği (Biraz daha net)
    sorgu2 = "İtalya devletinin yönetim merkezi neresidir?"
    
    print(f"\nSoru 2: {sorgu2}")
    cevap, skor = engine.find_best_match(sorgu2, database, min_score=0.25)
    print(f"Cevap: {cevap}")
    print(f"Skor: {skor:.4f}")