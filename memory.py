import sqlite3
import os
import logging
from logger import log_event
import re

logger = logging.getLogger(__name__)

class MemoryManager:
    """
    SQLite veritabanı bağlantısını ve yönetimini sağlar.
    """
    
    def __init__(self, db_path="db/project.db", schema_path="db_schema.sql"):
        self.db_path = db_path
        self.schema_path = schema_path
        self.conn = None
        self.cursor = None
        self.last_interaction_id = None 
        self.profile_txt_path = "user_profile.txt" # Hafta 12 değişkeni

        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.connect()
        self.initialize_db()
        
        # Uygulama başlarken mevcut profili TXT'ye dök
        self._mirror_to_txt()
        
    def connect(self):
        """Veritabanı bağlantısını kurar."""
        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row 
            self.cursor = self.conn.cursor()
            log_event("INFO", f"SQLite veritabanina baglandi: {self.db_path}", __name__)
        except sqlite3.Error as e:
            log_event("CRITICAL", f"Veritabanı baglanti hatasi: {e}", __name__)
            
    def initialize_db(self):
        """Veritabanı tablolarını oluşturur."""
        if os.path.exists(self.schema_path):
            try:
                with open(self.schema_path, 'r', encoding='utf-8') as f:
                    sql_script = f.read()
                self.cursor.executescript(sql_script)
                self.conn.commit()
                log_event("INFO", "Veritabanı tablolari yuklendi.", __name__)
            except sqlite3.Error as e:
                log_event("ERROR", f"Sema hatasi: {e}", __name__)

        # Hafta 12: Profil tablosu şemada yoksa burada oluşturulur (Garanti altına alma)
        try:
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_profile (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)
            self.conn.commit()
        except sqlite3.Error as e:
            log_event("ERROR", f"Profil tablosu olusturma hatasi: {e}", __name__)

    def normalize_query(self, query: str) -> str:
        """Sorguyu temizler."""
        if not query:
            return ""
        cleaned = re.sub(r'[^\w\s]', ' ', query) 
        return ' '.join(cleaned.lower().split()).strip()

    def save_interaction(self, user_input, assistant_response):
        """Etkileşimi kaydeder."""
        try:
            self.cursor.execute("""
                INSERT INTO interactions (user_input, response_text) 
                VALUES (?, ?)
            """, (user_input, assistant_response))
            self.conn.commit()
            self.last_interaction_id = self.cursor.lastrowid
            return self.last_interaction_id
        except sqlite3.Error as e:
            log_event("ERROR", f"Etkilesim kaydetme hatasi: {e}", __name__)
            return None
    
    def save_feedback(self, interaction_id, feedback_type, score):
        """Geri bildirimi kaydeder."""
        try:
            self.cursor.execute('''
                INSERT INTO feedback (interaction_id, feedback_type, score) VALUES (?,?,?)''',
                (interaction_id, feedback_type, score))
            self.conn.commit()
        except sqlite3.Error as e:
            log_event("ERROR", f"Geri bildirim hatasi: {e}", __name__)

    def promote_to_memory(self, user_query, bot_response):
        """Kalıcı hafızaya kayıt (LTM)."""
        normalized_key = self.normalize_query(user_query)
        try:
            self.cursor.execute("""
                INSERT OR REPLACE INTO memory (key, value, status, created_at)
                VALUES (?, ?, 'valid', CURRENT_TIMESTAMP)
            """, (normalized_key, bot_response))
            self.conn.commit()
            log_event("INFO", f"LTM Kaydi Basarili: {normalized_key}", __name__)
            return True
        except Exception as e:
            log_event("ERROR", f"LTM Kayit Hatasi: {e}", __name__)
            return False

    def read_from_memory(self, query: str) -> str:
        """Hafızadan okuma."""
        normalized_key = self.normalize_query(query)
        try:
            self.cursor.execute('''
                SELECT value FROM memory
                WHERE key = ? AND status = 'valid'
                ORDER BY created_at DESC LIMIT 1
            ''', (normalized_key,))
            row = self.cursor.fetchone()
            if row:
                return row['value']
            return None
        except sqlite3.Error as e:
            log_event("ERROR", f"Okuma Hatasi: {e}", __name__)
            return None

    def add_task(self, task):
        """Görev ekleme."""
        try:
            self.cursor.execute("INSERT INTO todo_list (task, status) VALUES (?, 'pending')", (task,))
            self.conn.commit()
            return True
        except Exception as e:
            log_event("ERROR", f"Gorev Ekleme Hatasi: {e}", __name__)
            return False

    def get_tasks(self):
        """Görevleri listeleme."""
        try:
            self.cursor.execute("SELECT id, task FROM todo_list WHERE status = 'pending'")
            return self.cursor.fetchall()
        except Exception as e:
            log_event("ERROR", f"Gorev Listeleme Hatasi: {e}", __name__)
            return []

    def close(self):
        if self.conn:
            self.conn.close()
            log_event("INFO", "Veritabanı baglantisi kapatildi.", __name__)

    # --- TXT AYNA TOOL BAŞLANGIÇ ---
    def _mirror_to_txt(self):
        """Veritabanındaki profili TXT dosyasına senkronize eder."""
        try:
            self.cursor.execute("SELECT key, value FROM user_profile")
            rows = self.cursor.fetchall()
            
            with open(self.profile_txt_path, "w", encoding="utf-8") as f:
                f.write("=== CANLI PROFiL TAKiBi ===\n\n")
                if not rows:
                    f.write("Henuz profil verisi kaydedilmedi.\n")
                else:
                    for row in rows:
                        f.write(f"{row['key'].upper()}: {row['value']}\n")
                        f.write("-" * 20 + "\n")
        except Exception as e:
            log_event("WARNING", f"TXT Mirror Hatasi: {e}", "Memory")
    # --- TXT AYNA TOOL SONU ---

    def set_profile(self, key, value):
        """Profil verisini DB'ye yazar ve TXT aynasını günceller."""
        try:
            self.cursor.execute("INSERT OR REPLACE INTO user_profile (key, value) VALUES (?, ?)", (key, value))
            self.conn.commit()
            self._mirror_to_txt() # Mirror tetiklendi
            return True
        except Exception as e:
            log_event("ERROR", f"Profil Kayit Hatasi: {e}", "Memory")
            return False

    def get_profile(self):
        """Tüm profili sözlük (dictionary) olarak döndürür."""
        try:
            self.cursor.execute("SELECT key, value FROM user_profile")
            return {row['key']: row['value'] for row in self.cursor.fetchall()}
        except Exception as e:
            log_event("ERROR", f"Profil getirme hatasi: {e}", "Memory")
            return {}
        
    #HAFTA13 Hafızadan Silme Fonk
    def delete_last_memory(self):
        try:
            # En son eklenen profil bilgisini tamamen sil (Boşaltma yapma, SİL)
            self.cursor.execute("SELECT key FROM user_profile ORDER BY rowid DESC LIMIT 1")
            res = self.cursor.fetchone()
            if res:
                self.cursor.execute("DELETE FROM user_profile WHERE key = ?", (res[0],))
            
            # Kalıcı hafızayı sil
            self.cursor.execute("DELETE FROM memory WHERE rowid = (SELECT MAX(rowid) FROM memory)")
            self.conn.commit()
            self._mirror_to_txt()
            return True
        except:
            return False