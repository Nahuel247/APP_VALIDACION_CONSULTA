CREATE TABLE IF NOT EXISTS predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_text TEXT NOT NULL,
    normalized_text TEXT NOT NULL UNIQUE,
    predicted_label TEXT NOT NULL,
    confidence REAL NOT NULL,
    confidence_valida REAL NOT NULL DEFAULT 0,
    confidence_no_valida REAL NOT NULL DEFAULT 0,
    times_asked INTEGER NOT NULL DEFAULT 1,
    upvotes INTEGER NOT NULL DEFAULT 0,
    downvotes INTEGER NOT NULL DEFAULT 0,
    interactions INTEGER NOT NULL DEFAULT 1,
    is_hidden INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
