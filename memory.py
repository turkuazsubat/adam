import sqlite3

class MemoryManager:
    def __init__(self, db_path):
        self.conn = sqlite3.connect(db_path)
        self.create_table()

    def create_table(self):
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS memory(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_input TEXT,
            response TEXT
        )
        """)

    def save_interaction(self, user_input, response):
        self.conn.execute("INSERT INTO memory (user_input, response) VALUES (?, ?)", (user_input, response))
        self.conn.commit()

    def get_last_user_input(self):
        cur = self.conn.cursor()
        cur.execute("SELECT user_input FROM memory ORDER BY id DESC LIMIT 1")
        row = cur.fetchone()
        return row[0] if row else ""
