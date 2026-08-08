"""Shared SQLite connection helper for the storage domain."""

import sqlite3
from pathlib import Path

DB_PATH = Path.home() / ".hebtranscriber" / "hebtranscriber.db"


def connect(schema: str, db_path: Path = DB_PATH) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.executescript(schema)
    return conn
