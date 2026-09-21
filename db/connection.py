"""Database connection helper.

Provides get_conn() context manager for fresh SQLite connections
with foreign keys enabled, and run_migrations() for schema setup.
"""

import os
import sqlite3
from contextlib import contextmanager
from typing import Generator

from db.migrations import run_migrations

# Database file lives in data/ under the project root
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DATA_DIR = os.path.join(_PROJECT_ROOT, "data")
DB_PATH = os.path.join(_DATA_DIR, "tracker.db")


def _ensure_data_dir() -> None:
    """Create the data/ directory if it does not exist."""
    os.makedirs(_DATA_DIR, exist_ok=True)


@contextmanager
def get_conn(db_path: str | None = None) -> Generator[sqlite3.Connection, None, None]:
    """Yield a fresh SQLite connection with foreign keys enabled.

    Args:
        db_path: Override path for testing. Defaults to data/tracker.db.
    """
    _ensure_data_dir()
    path = db_path or DB_PATH
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
    finally:
        conn.close()


def init_db(db_path: str | None = None) -> None:
    """Run migrations on the database, creating it if needed.

    Args:
        db_path: Override path for testing.
    """
    with get_conn(db_path) as conn:
        run_migrations(conn)
