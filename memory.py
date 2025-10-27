import sqlite3
import os
import logging
from logger import log_event # logger modülünden log_event'i içe aktar

logger = logging.getLogger(__name__)

class MemoryManager:
    """
    SQLite veritabanı bağlantısını ve yönetimini sağlar.
    Hafıza, etkileşimler ve geri bildirim tablolarını yönetir.
    """
    
    def __init__(self, db_path="db/project.db", schema_path="db_schema.sql"):
        # db_path: Veritabanı dosyasının yolu (db/project.db)
        # schema_path: Tabloları oluşturan SQL dosyasının yolu
        self.db_path = db_path
        self.schema_path = schema_path
        self.conn = None
        self.cursor = None
        
        # Veritabanı klasörünün varlığını kontrol et
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        self.connect()
        self.initialize_db()
        
    def connect(self):
        """Veritabanı bağlantısını kurar."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            log_event("INFO", f"SQLite veritabanına bağlandı: {self.db_path}", __name__)
        except sqlite3.Error as e:
            log_event("CRITICAL", f"Veritabanı bağlantı hatası: {e}", __name__)
            
    def initialize_db(self):
        """Veritabanı tablolarını oluşturur (Eğer yoksa)."""
        if not os.path.exists(self.schema_path):
            log_event("CRITICAL", f"Veritabanı şema dosyası bulunamadı: {self.schema_path}", __name__)
            return

        try:
            with open(self.schema_path, 'r', encoding='utf-8') as f:
                sql_script = f.read()
            
            # execute_script, birden fazla SQL komutunu çalıştırır
            self.cursor.executescript(sql_script)
            self.conn.commit()
            log_event("INFO", "Veritabanı tabloları başarıyla oluşturuldu/kontrol edildi.", __name__)

        except sqlite3.Error as e:
            log_event("ERROR", f"Veritabanı şema çalıştırma hatası: {e}", __name__)
            
    def close(self):
        """Bağlantıyı kapatır."""
        if self.conn:
            self.conn.close()
            log_event("INFO", "Veritabanı bağlantısı kapatıldı.", __name__)

    # --- Hafta 3'te Eklenecek Temel CRUD Metodları ---
    
    def save_interaction(self, user_input, assistant_response):
        """main.py'den çağrılır: Etkileşimi Interactions tablosuna kaydeder."""
        # Şimdilik sadece minimal veri kaydı yapıyoruz.
        # İleride NLU, model versiyonu vb. eklenecek.
        try:
            self.cursor.execute("""
                INSERT INTO interactions (user_input, response_text) 
                VALUES (?, ?)
            """, (user_input, assistant_response))
            self.conn.commit()
            log_event("DEBUG", "Etkileşim interactions tablosuna kaydedildi.", __name__)
            return self.cursor.lastrowid # Son eklenen kaydın ID'sini döndür
        except sqlite3.Error as e:
            log_event("ERROR", f"Etkileşim kaydetme hatası: {e}", __name__)
            return None

    # Not: Geri kalan Hafıza metotları Hafta 4 ve sonrasında eklenecek.
    
# main.py'deki memory = MemoryManager() çağrısı, bu sınıfı kullanacak.