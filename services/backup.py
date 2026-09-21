"""Backup service — auto backup, CSV export, restore.

Uses sqlite3's backup API for consistent copies. See spec Section 11.
"""

from __future__ import annotations

import csv
import io
import os
import shutil
import sqlite3
import zipfile
from datetime import datetime
from typing import Optional

from db import repository as repo
from db.connection import DB_PATH, get_conn
from db.migrations import run_migrations


# Backup directory
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKUP_DIR = os.path.join(_PROJECT_ROOT, "backups")


def _ensure_backup_dir() -> None:
    """Create the backups directory if needed."""
    os.makedirs(BACKUP_DIR, exist_ok=True)


def auto_backup(today_iso: str, keep: int = 30) -> str | None:
    """Create a daily backup if one doesn't exist yet for today.

    Uses sqlite3's backup API for consistency.
    Prunes old backups beyond `keep`.

    Args:
        today_iso: Today's date as YYYY-MM-DD.
        keep: Number of daily backups to retain.

    Returns:
        Path to the backup file, or None if already backed up today or DB missing.
    """
    if not os.path.exists(DB_PATH):
        return None

    _ensure_backup_dir()
    backup_name = f"tracker_{today_iso}.db"
    backup_path = os.path.join(BACKUP_DIR, backup_name)

    if os.path.exists(backup_path):
        return None

    # Use sqlite3 backup API
    source = sqlite3.connect(DB_PATH)
    dest = sqlite3.connect(backup_path)
    try:
        source.backup(dest)
    finally:
        dest.close()
        source.close()

    # Prune old backups
    _prune_backups(keep)

    return backup_path


def backup_now() -> str:
    """Create an immediate backup with timestamp.

    Returns:
        Path to the backup file.
    """
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError("Database file not found")

    _ensure_backup_dir()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"tracker_manual_{timestamp}.db"
    backup_path = os.path.join(BACKUP_DIR, backup_name)

    source = sqlite3.connect(DB_PATH)
    dest = sqlite3.connect(backup_path)
    try:
        source.backup(dest)
    finally:
        dest.close()
        source.close()

    return backup_path


def list_backups() -> list[dict]:
    """Return a list of backup files with metadata.

    Returns list of dicts with keys: name, path, size_mb, created.
    """
    _ensure_backup_dir()
    backups = []
    for name in sorted(os.listdir(BACKUP_DIR), reverse=True):
        if name.endswith(".db"):
            path = os.path.join(BACKUP_DIR, name)
            size = os.path.getsize(path)
            created = datetime.fromtimestamp(os.path.getctime(path))
            backups.append({
                "name": name,
                "path": path,
                "size_mb": round(size / (1024 * 1024), 2),
                "created": created.strftime("%Y-%m-%d %H:%M"),
            })
    return backups


def export_csv_zip() -> bytes:
    """Export all database tables as CSV files in a zip archive.

    Returns:
        Zip file contents as bytes.
    """
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        with get_conn() as conn:
            table_names = repo.get_all_table_names(conn)
            for table_name in table_names:
                rows = repo.export_table_as_dicts(conn, table_name)
                if not rows:
                    # Empty table — just write headers
                    cols = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
                    headers = [c[1] for c in cols]
                    csv_buf = io.StringIO()
                    writer = csv.DictWriter(csv_buf, fieldnames=headers)
                    writer.writeheader()
                    zf.writestr(f"{table_name}.csv", csv_buf.getvalue())
                else:
                    csv_buf = io.StringIO()
                    writer = csv.DictWriter(csv_buf, fieldnames=rows[0].keys())
                    writer.writeheader()
                    writer.writerows(rows)
                    zf.writestr(f"{table_name}.csv", csv_buf.getvalue())

    return buf.getvalue()


def restore_from(path_or_bytes) -> None:
    """Restore the database from a backup file.

    Validates the file, backs up current DB, then replaces it.

    Args:
        path_or_bytes: Path to a .db file or bytes content.

    Raises:
        ValueError: If the file is not a valid tracker database.
    """
    # Write bytes to temp file if needed
    if isinstance(path_or_bytes, bytes):
        _ensure_backup_dir()
        temp_path = os.path.join(BACKUP_DIR, "_temp_restore.db")
        with open(temp_path, "wb") as f:
            f.write(path_or_bytes)
        source_path = temp_path
    else:
        source_path = path_or_bytes

    # Validate
    try:
        test_conn = sqlite3.connect(source_path)
        test_conn.execute("SELECT version FROM schema_version")
        test_conn.close()
    except Exception:
        raise ValueError("Invalid database file: missing schema_version table")

    # Backup current DB before restoring
    if os.path.exists(DB_PATH):
        _ensure_backup_dir()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        pre_restore = os.path.join(BACKUP_DIR, f"pre_restore_{timestamp}.db")
        shutil.copy2(DB_PATH, pre_restore)

    # Replace the DB
    shutil.copy2(source_path, DB_PATH)

    # Run migrations in case the restored DB is from an older version
    with get_conn() as conn:
        run_migrations(conn)

    # Clean up temp file
    if isinstance(path_or_bytes, bytes):
        os.remove(source_path)


def _prune_backups(keep: int) -> None:
    """Delete the oldest backup files beyond the keep limit."""
    backups = []
    for name in os.listdir(BACKUP_DIR):
        if name.startswith("tracker_") and name.endswith(".db") and not name.startswith("tracker_manual"):
            path = os.path.join(BACKUP_DIR, name)
            backups.append((name, path, os.path.getctime(path)))

    # Sort by creation time, oldest first
    backups.sort(key=lambda x: x[2])

    # Delete oldest beyond keep
    while len(backups) > keep:
        _, path, _ = backups.pop(0)
        os.remove(path)
