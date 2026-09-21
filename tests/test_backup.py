"""Tests for backup service — spec Section 12 (Backup).

- auto_backup creates one file per day and prunes old ones.
- Restore of an invalid file is rejected and leaves the DB unchanged.
"""

import os
import sqlite3
import pytest

from db.migrations import run_migrations
from services import backup


def test_auto_backup_creates_file(db_path, tmp_path):
    """auto_backup creates a file for today."""
    # Create a real DB first
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    run_migrations(conn)
    conn.execute("INSERT INTO task (title) VALUES ('test')")
    conn.commit()
    conn.close()

    # Override paths
    original_db = backup.DB_PATH
    original_dir = backup.BACKUP_DIR
    backup.DB_PATH = db_path
    backup.BACKUP_DIR = str(tmp_path / "backups")

    try:
        path = backup.auto_backup("2025-01-10")
        assert path is not None
        assert os.path.exists(path)
        assert "2025-01-10" in os.path.basename(path)

        # Second call same day — no new backup
        path2 = backup.auto_backup("2025-01-10")
        assert path2 is None
    finally:
        backup.DB_PATH = original_db
        backup.BACKUP_DIR = original_dir


def test_auto_backup_prunes_old(db_path, tmp_path):
    """auto_backup prunes beyond keep limit."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    run_migrations(conn)
    conn.close()

    original_db = backup.DB_PATH
    original_dir = backup.BACKUP_DIR
    backup.DB_PATH = db_path
    backup.BACKUP_DIR = str(tmp_path / "backups")

    try:
        # Create 5 daily backups with keep=3
        for day in range(1, 6):
            date = f"2025-01-{day:02d}"
            backup.auto_backup(date, keep=3)

        backup_files = [f for f in os.listdir(backup.BACKUP_DIR) if f.endswith(".db")]
        assert len(backup_files) <= 3
    finally:
        backup.DB_PATH = original_db
        backup.BACKUP_DIR = original_dir


def test_restore_invalid_file_rejected(db_path, tmp_path):
    """Restore of an invalid file is rejected."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    run_migrations(conn)
    conn.close()

    original_db = backup.DB_PATH
    original_dir = backup.BACKUP_DIR
    backup.DB_PATH = db_path
    backup.BACKUP_DIR = str(tmp_path / "backups")

    try:
        # Try restoring garbage bytes
        with pytest.raises(ValueError, match="Invalid database"):
            backup.restore_from(b"not a database file at all")
    finally:
        backup.DB_PATH = original_db
        backup.BACKUP_DIR = original_dir


def test_restore_valid_file(db_path, tmp_path):
    """Restore from a valid backup works."""
    # Create original DB
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    run_migrations(conn)
    conn.execute("INSERT INTO task (title) VALUES ('original')")
    conn.commit()
    conn.close()

    original_db = backup.DB_PATH
    original_dir = backup.BACKUP_DIR
    backup.DB_PATH = db_path
    backup.BACKUP_DIR = str(tmp_path / "backups")

    try:
        # Backup
        backup_path = backup.backup_now()

        # Modify DB
        conn = sqlite3.connect(db_path)
        conn.execute("DELETE FROM task")
        conn.commit()
        conn.close()

        # Restore
        backup.restore_from(backup_path)

        # Verify
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT title FROM task").fetchone()
        assert row[0] == "original"
        conn.close()
    finally:
        backup.DB_PATH = original_db
        backup.BACKUP_DIR = original_dir
