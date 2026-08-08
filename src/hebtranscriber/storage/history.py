"""Stage 5: local session history with full-text search (SQLite FTS5)."""

import time
from dataclasses import dataclass
from pathlib import Path

from hebtranscriber.storage._db import DB_PATH, connect

SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at REAL NOT NULL,
    duration_s REAL NOT NULL,
    raw_text TEXT NOT NULL,
    clean_text TEXT NOT NULL,
    words_per_minute REAL NOT NULL
);
CREATE VIRTUAL TABLE IF NOT EXISTS sessions_fts USING fts5(clean_text);
"""


@dataclass
class Session:
    id: int
    created_at: float
    duration_s: float
    raw_text: str
    clean_text: str
    words_per_minute: float


def save_session(raw_text: str, clean_text: str, duration_s: float, db_path: Path = DB_PATH) -> int:
    words_per_minute = (len(clean_text.split()) / duration_s * 60) if duration_s > 0 else 0.0
    with connect(SCHEMA, db_path) as conn:
        cursor = conn.execute(
            "INSERT INTO sessions (created_at, duration_s, raw_text, clean_text, words_per_minute) "
            "VALUES (?, ?, ?, ?, ?)",
            (time.time(), duration_s, raw_text, clean_text, words_per_minute),
        )
        session_id = cursor.lastrowid
        conn.execute(
            "INSERT INTO sessions_fts (rowid, clean_text) VALUES (?, ?)",
            (session_id, clean_text),
        )
        return session_id


def search(query: str, db_path: Path = DB_PATH) -> list[Session]:
    with connect(SCHEMA, db_path) as conn:
        rows = conn.execute(
            "SELECT s.id, s.created_at, s.duration_s, s.raw_text, s.clean_text, s.words_per_minute "
            "FROM sessions_fts f JOIN sessions s ON s.id = f.rowid "
            "WHERE sessions_fts MATCH ? ORDER BY s.created_at DESC",
            (query,),
        ).fetchall()
    return [Session(*row) for row in rows]


def recent_sessions(limit: int = 10, db_path: Path = DB_PATH) -> list[Session]:
    with connect(SCHEMA, db_path) as conn:
        rows = conn.execute(
            "SELECT id, created_at, duration_s, raw_text, clean_text, words_per_minute "
            "FROM sessions ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [Session(*row) for row in rows]


def stats(db_path: Path = DB_PATH) -> dict:
    sessions = recent_sessions(limit=-1, db_path=db_path)  # SQLite: negative LIMIT means no limit
    total_words = sum(len(s.clean_text.split()) for s in sessions)
    return {
        "total_sessions": len(sessions),
        "total_words": total_words,
        "last_session_words": len(sessions[0].clean_text.split()) if sessions else 0,
        "average_words_per_minute": (
            sum(s.words_per_minute for s in sessions) / len(sessions) if sessions else 0.0
        ),
    }
