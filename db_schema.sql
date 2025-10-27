-- Versiyon Takibi
CREATE TABLE versions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  component TEXT,
  version TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Kaynak Bilgisi
CREATE TABLE sources (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  url TEXT,
  title TEXT,
  fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Kalıcı Hafıza
CREATE TABLE memory (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  key TEXT,
  value TEXT,
  provenance TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  created_by TEXT,
  status TEXT DEFAULT 'valid',
  version INTEGER DEFAULT 1
);

-- Etkileşim Kayıtları
CREATE TABLE interactions (
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
CREATE TABLE feedback (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  interaction_id INTEGER,
  feedback_type TEXT,
  score INTEGER,
  comment TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);