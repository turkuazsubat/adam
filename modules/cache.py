import sqlite3
import sys

class CacheManager:
    def __init__(self, db_path="db/project.db"):
        self.db_path = db_path
        print("--- Cache (Önbellek) Sistemi Başlatıldı ---", flush=True)
        self._init_db()

    def _init_db(self):
        """Önbellek tablosunu oluşturur (Yoksa)"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS response_cache (
                    query_text TEXT PRIMARY KEY,
                    response_text TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"❌ Cache DB Hatası: {e}", flush=True)

    def get_cached_response(self, user_input):
        """Sorulan soru daha önce sorulmuş mu?"""
        if not user_input: return None
        
        normalized_input = user_input.strip().lower()
        print(f"🔍 CACHE ARANIYOR: '{normalized_input}'", flush=True)
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT response_text FROM response_cache WHERE query_text = ?", (normalized_input,))
            result = cursor.fetchone()
            conn.close()
            
            if result:
                print(f"⚡ CACHE HIT (BULUNDU)! Cevap veritabanından dönüyor...", flush=True)
                return result[0]
            else:
                print("❌ Cache'de yok. (Yapay zeka devreye girecek)", flush=True)
                return None
        except Exception as e:
            print(f"❌ Cache Okuma Hatası: {e}", flush=True)
            return None

    def save_to_cache(self, user_input, response_text):
        """Yeni üretilen cevabı kaydeder"""
        if not user_input or not response_text:
            return

        normalized_input = user_input.strip().lower()
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Varsa güncelle, yoksa ekle (REPLACE)
            cursor.execute("INSERT OR REPLACE INTO response_cache (query_text, response_text) VALUES (?, ?)", 
                           (normalized_input, response_text))
            conn.commit()
            conn.close()
            print(f"💾 CACHE SAVED: '{normalized_input}' veritabanına kaydedildi.", flush=True)
        except Exception as e:
            print(f"❌ Cache Yazma Hatası: {e}", flush=True)