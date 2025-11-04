import sqlite3
import os
import logging
from logger import log_event # logger modülünden log_event'i içe aktar
import re

logger = logging.getLogger(__name__)


# --- KRİTİK NORMALLEŞTİRME FONKSİYONU ---
def normalize_query(query: str) -> str:
    """Hafıza kaydı için sorguyu temizler: Küçük harf yapar ve noktalama işaretlerini kaldırır."""
    if not query:
        return ""
    # Alfanümerik ve boşluk dışındaki her şeyi boşluk yap
    cleaned = re.sub(r'[^\w\s]', ' ', query) 
    # Fazla boşlukları sil ve küçük harf yap
    return ' '.join(cleaned.lower().split()).strip()


# main.py'deki memory = MemoryManager() çağrısı, bu sınıfı kullanacak.
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
        
        #Hafta 4 Yeni eklendi, Son kaydedilen etkileşim ID sini tutar,(feedback için kritik)
        self.last_interaction_id = None 

        # Veritabanı klasörünün varlığını kontrol et
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        self.connect()
        self.initialize_db()
        
    def connect(self):
        """Veritabanı bağlantısını kurar."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
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
        '''Etkileşimli Interaction tablosuna kaydeder ve last_interaction_id'yi günceller'''
        
        try:
            self.cursor.execute("""
                INSERT INTO interactions (user_input, response_text) 
                VALUES (?, ?)
            """, (user_input, assistant_response))
            self.conn.commit()

            #Hafta4 Kritik Güncelleme, Son ID yi kaydetme
            self.last_interaction_id = self.cursor.lastrowid

            log_event("DEBUG", f"Etkileşim kaydedildi. ID: {self.last_interaction_id}",__name__)

            return self.last_interaction_id
        
        except sqlite3.Error as e:
            log_event("ERROR", f"Etkileşim kaydetme hatası: {e}", __name__)
            return None
    
    def save_feedback(self,interaction_id, feedback_type, score):
        '''Kullanıcı geri bildirimini feedback tablosuna kaydeder.'''

        try:
            self.cursor.execute('''
                INSERT INTO feedback (interaction_id, feedback_type, score) VALUES (?,?,?)''',
                (interaction_id,feedback_type,score))
            self.conn.commit()
            log_event("INFO", f"Geri bildirim kaydedildi (ID: {interaction_id}, Tip: {feedback_type}).", __name__)

        except sqlite3.Error as e:
            log_event("ERROR", f"Geri bildirim kaydetme hatası: {e}", __name__)

    
    def promote_to_memory(self,interaction_id):
        ''' Lite RLHF V1: Bir etkileşimi, kalıcı hafızaya(memory) tablosuna taşır. 
            (Sadece olumlu/önemli geri bildirimlerde çağrılır)
        '''
        try:
            # 1. Interaction tablosundan sorgu ve cevap çek
            self.cursor.execute("SELECT user_input, response_text FROM interactions WHERE id =?", (interaction_id,))
            row = self.cursor.fetchone()

            if row:
                user_input = row['user_input'].strip()
                response_text = row['response_text'].strip()

                # 2. Memory tablosuna kaydet (Hafta 4 V! kuralı: Key= Sorgu, Value=Cevap)
                self.cursor.execute(''' 
                    INSERT INTO memory(key,value,created_by,provenance) VALUES (?,?,?,?)''',
                    (user_input,response_text,'user_feedback','interaction_id ' + str(interaction_id)))
                
                self.conn.commit()
                log_event("WARNING", f"!!! KRİTİK ÖĞRENME !!! Etkileşim ID {interaction_id} kalıcı hafızaya taşındı.", __name__)
            else:
                log_event("WARNING", f"ID {interaction_id} ile etkileşim bulunamadığı için hafızaya taşınamadı.", __name__)

        except sqlite3.Error as e:
            log_event("ERROR", f"Hafızaya taşıma hatası: {e}", __name__)
        
    
    def invalidate_memory(self, interaction_id):
        """
        Lite RLHF V1: Olumsuz geri bildirime karşı hafızadaki ilgili kaydı geçersiz kılar.
        """

        try:
            # Önce bu etkileşimden türetilmiş bir hafıza kaydı var mı diye bak.
            provenance_check = 'interaction_id ' + str(interaction_id)

            self.cursor.execute('''
                UPDATE memory
                SET status = 'invalid', version = version + 1
                WHERE provenance = ? AND status = 'valid'
                ''',(provenance_check,))
            self.conn.commit()

            if self.cursor.rowcount > 0:
                log_event("WARNING", f"Hafıza kaydı geçersiz kılındı (İlgili Etkileşim ID: {interaction_id}).", __name__)
            else:
                log_event("DEBUG", f"ID {interaction_id} ile ilgili geçerli bir hafıza kaydı bulunamadı.", __name__)
                
        except sqlite3.Error as e:
            log_event("ERROR", f"Hafıza geçersiz kılma hatası: {e}", __name__)

    #Hafta4: Hafızadan Okuma

    def read_from_memory(self, query: str) -> str:
        '''Kalıcı hafızadan (memory tablosu) geçerli bilgiyi çeker'''

        cleaned_query = query.strip()

        try:
            self.cursor.execute('''
                SELECT value FROM memory
                WHERE key = ? AND status = 'valid'
                ORDER BY created_at DESC LIMIT 1
                                ''', (cleaned_query,))
            
            row = self.cursor.fetchone()

            if row:
                log_event("DEBUG", f"Hafızadan bilgi bulundu: {query}", __name__)
                return row['value']
            return None
            
        except sqlite3.Error as e:
            log_event("ERROR", f"Hafızadan okuma hatası: {e}", __name__)
            return None


    
    
