"""Stage 5: personal vocabulary — names/terms injected into cleanup prompts
so the LLM cleanup step spells them correctly."""

from pathlib import Path

from hebtranscriber.storage._db import DB_PATH, connect

SCHEMA = "CREATE TABLE IF NOT EXISTS terms (term TEXT PRIMARY KEY)"


def add_term(term: str, db_path: Path = DB_PATH) -> None:
    with connect(SCHEMA, db_path) as conn:
        conn.execute("INSERT OR IGNORE INTO terms (term) VALUES (?)", (term.strip(),))


def remove_term(term: str, db_path: Path = DB_PATH) -> None:
    with connect(SCHEMA, db_path) as conn:
        conn.execute("DELETE FROM terms WHERE term = ?", (term.strip(),))


def list_terms(db_path: Path = DB_PATH) -> list[str]:
    with connect(SCHEMA, db_path) as conn:
        return [row[0] for row in conn.execute("SELECT term FROM terms ORDER BY term")]
