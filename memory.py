import sqlite3
from datetime import datetime
import os

class MemoryManager:
    def __init__(self, db_path="db/project.db"):
        self.db_path = db_path
        if not os.path.exists("db"):
            os.makedirs("db")
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                user_input TEXT,
                assistant_response TEXT
            )
        """)
        conn.commit()
        conn.close()

    def save_interaction(self, user_input, assistant_response):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO conversations (timestamp, user_input, assistant_response) VALUES (?, ?, ?)",
            (datetime.now().isoformat(), user_input, assistant_response)
        )
        conn.commit()
        conn.close()

    def get_last_interactions(self, limit=5):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM conversations ORDER BY id DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        conn.close()
        return rows
