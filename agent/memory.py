"""
SQLite memory for the agent.

We store papers the agent has already shown the user.
This prevents repeated results across runs.
"""

import sqlite3
from datetime import date
from pathlib import Path


def strip_version(arxiv_id: str) -> str:
    """
    Remove the version suffix from an arXiv ID.

    Example: "2610.03715v1" -> "2610.03715"
    Example: "cs.AI/0601001v2" -> "cs.AI/0601001"
    """
    return arxiv_id.rsplit("v", 1)[0]


def _get_connection(db_path: str) -> sqlite3.Connection:
    """
    Open a connection and make sure the schema exists.

    We use CREATE TABLE IF NOT EXISTS so this is safe to call often.
    """
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS seen_papers (
            arxiv_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            first_seen DATE NOT NULL
        )
        """
    )
    conn.commit()
    return conn


def check_seen(arxiv_id: str, db_path: str = "data/memory.db") -> bool:
    """
    Return True if the paper has been seen before.
    """
    clean_id = strip_version(arxiv_id)
    conn = _get_connection(db_path)
    try:
        cur = conn.execute(
            "SELECT 1 FROM seen_papers WHERE arxiv_id = ?",
            (clean_id,),
        )
        return cur.fetchone() is not None
    finally:
        conn.close()


def mark_seen(
    arxiv_id: str,
    title: str,
    db_path: str = "data/memory.db",
) -> None:
    """
    Store a paper as seen. Safe to call twice.

    INSERT OR IGNORE keeps the original first_seen date
    if the row already exists.
    """
    clean_id = strip_version(arxiv_id)
    conn = _get_connection(db_path)
    try:
        conn.execute(
            """
            INSERT OR IGNORE INTO seen_papers (arxiv_id, title, first_seen)
            VALUES (?, ?, ?)
            """,
            (clean_id, title, date.today().isoformat()),
        )
        conn.commit()
    finally:
        conn.close()


def count_seen(db_path: str = "data/memory.db") -> int:
    """Return the number of papers in memory. Useful for tests."""
    conn = _get_connection(db_path)
    try:
        cur = conn.execute("SELECT COUNT(*) FROM seen_papers")
        return cur.fetchone()[0]
    finally:
        conn.close()
