"""
Database Connection and Session Manager.
Ensures SQLite foreign key constraints are always enforced.
"""

import sqlite3
from contextlib import contextmanager
from backend.config import Config


def get_db_connection(db_path: str = None) -> sqlite3.Connection:
    """Returns a SQLite connection with Row factory and Foreign Keys enabled."""
    target_path = db_path or Config.DB_PATH
    conn = sqlite3.connect(target_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


@contextmanager
def get_db_cursor(db_path: str = None, commit: bool = False):
    """Context manager for safe database transactions."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    try:
        yield cursor
        if commit:
            conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()
