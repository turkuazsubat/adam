-- Versiyon Takibi
CREATE TABLE IF NOT EXISTS versions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  component TEXT,
  version TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Kaynak Bilgisi
CREATE TABLE IF NOT EXISTS sources (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  url TEXT,
  title TEXT,
  fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Kalıcı Hafıza (LTM)
CREATE TABLE IF NOT EXISTS memory (
  key TEXT PRIMARY KEY, -- ID yerine Key'i Primary yaptık ki tekrarı önleyelim
  value TEXT,
  provenance TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  created_by TEXT,
  status TEXT DEFAULT 'valid',
  version INTEGER DEFAULT 1
);

-- Etkileşim Kayıtları
CREATE TABLE IF NOT EXISTS interactions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  user_input TEXT,
  stt_confidence REAL,
  retrieved_sources TEXT,
  summary TEXT,
  response_text TEXT,
  model_version TEXT
);

-- Geri Bildirim Kayıtları
CREATE TABLE IF NOT EXISTS feedback (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  interaction_id INTEGER,
  feedback_type TEXT,
  score INTEGER,
  comment TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- EKSİK OLAN TABLO EKLENDİ: Görev Listesi
CREATE TABLE IF NOT EXISTS todo_list (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task TEXT,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);