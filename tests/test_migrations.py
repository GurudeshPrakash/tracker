"""Tests for database migrations."""

import sqlite3
from db.migrations import run_migrations, _get_current_version


def test_fresh_db_ends_at_version_1(db_conn):
    """A fresh database after migrations should be at version 1."""
    version = _get_current_version(db_conn)
    assert version == 1


def test_running_migrations_twice_is_safe(db_path):
    """Running migrations twice does not error or change schema version."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    run_migrations(conn)
    assert _get_current_version(conn) == 1

    # Run again — should be a no-op
    run_migrations(conn)
    assert _get_current_version(conn) == 1
    conn.close()


def test_all_tables_created(db_conn):
    """All expected tables exist after migration v1."""
    tables = db_conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
    ).fetchall()
    table_names = sorted([r[0] for r in tables])
    expected = sorted([
        "schema_version", "goal", "learning_item", "recurring_task",
        "task", "learning_session", "daily_update", "review",
    ])
    assert table_names == expected


def test_foreign_keys_enabled(db_conn):
    """PRAGMA foreign_keys is ON."""
    row = db_conn.execute("PRAGMA foreign_keys").fetchone()
    assert row[0] == 1


def test_task_table_has_correct_columns(db_conn):
    """Spot-check that the task table has the expected columns."""
    info = db_conn.execute("PRAGMA table_info(task)").fetchall()
    col_names = [row[1] for row in info]
    assert "title" in col_names
    assert "planned_date" in col_names
    assert "is_top3" in col_names
    assert "rollover_count" in col_names
    assert "completed_date" in col_names
