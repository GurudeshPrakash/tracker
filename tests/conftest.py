"""Shared test fixtures.

Provides a temporary migrated database for all tests.
Tests never touch data/tracker.db.
"""

import os
import sys
import sqlite3

import pytest

# Ensure project root is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.migrations import run_migrations


@pytest.fixture
def db_path(tmp_path):
    """Return a path to a temp database file."""
    return str(tmp_path / "test_tracker.db")


@pytest.fixture
def db_conn(db_path):
    """Yield a migrated SQLite connection for testing.

    Uses tmp_path so each test gets a fresh database.
    Foreign keys are enabled.
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    run_migrations(conn)
    yield conn
    conn.close()
