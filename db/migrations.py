"""Database migrations.

MIGRATIONS is a dict mapping version numbers to SQL strings.
run_migrations(conn) applies any unapplied migrations in order.
"""

import sqlite3

# ---------------------------------------------------------------------------
# Schema version 1 — full initial schema from spec Section 6.2
# ---------------------------------------------------------------------------
SCHEMA_V1_SQL = """
CREATE TABLE schema_version (
    version INTEGER NOT NULL
);
INSERT INTO schema_version (version) VALUES (1);

CREATE TABLE goal (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    title         TEXT NOT NULL,
    target_type   TEXT NOT NULL CHECK (target_type IN ('weekly_hours','total_hours')),
    target_hours  REAL NOT NULL CHECK (target_hours > 0),
    start_date    TEXT NOT NULL,
    target_date   TEXT,
    status        TEXT NOT NULL DEFAULT 'active'
                  CHECK (status IN ('active','done','paused','dropped')),
    created_at    TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);

CREATE TABLE learning_item (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    skill         TEXT NOT NULL,
    resource      TEXT NOT NULL,
    resource_type TEXT NOT NULL DEFAULT 'course'
                  CHECK (resource_type IN ('course','book','video','article','practice','project','other')),
    status        TEXT NOT NULL DEFAULT 'in_progress'
                  CHECK (status IN ('planned','in_progress','done','paused')),
    goal_id       INTEGER REFERENCES goal(id) ON DELETE SET NULL,
    created_at    TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);

CREATE TABLE recurring_task (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    title            TEXT NOT NULL,
    priority         TEXT NOT NULL DEFAULT 'medium' CHECK (priority IN ('high','medium','low')),
    category         TEXT NOT NULL DEFAULT 'work'   CHECK (category IN ('work','learning','personal')),
    goal_id          INTEGER REFERENCES goal(id) ON DELETE SET NULL,
    learning_item_id INTEGER REFERENCES learning_item(id) ON DELETE SET NULL,
    estimated_min    INTEGER,
    rule             TEXT NOT NULL CHECK (rule IN ('daily','weekdays','weekly','monthly')),
    weekday          INTEGER CHECK (weekday BETWEEN 0 AND 6),
    day_of_month     INTEGER CHECK (day_of_month BETWEEN 1 AND 31),
    start_date       TEXT NOT NULL,
    end_date         TEXT,
    active           INTEGER NOT NULL DEFAULT 1,
    last_generated   TEXT
);

CREATE TABLE task (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    title            TEXT NOT NULL,
    notes            TEXT,
    planned_date     TEXT,
    due_date         TEXT,
    priority         TEXT NOT NULL DEFAULT 'medium' CHECK (priority IN ('high','medium','low')),
    category         TEXT NOT NULL DEFAULT 'work'   CHECK (category IN ('work','learning','personal')),
    goal_id          INTEGER REFERENCES goal(id) ON DELETE SET NULL,
    learning_item_id INTEGER REFERENCES learning_item(id) ON DELETE SET NULL,
    parent_task_id   INTEGER REFERENCES task(id) ON DELETE CASCADE,
    recurring_id     INTEGER REFERENCES recurring_task(id) ON DELETE SET NULL,
    status           TEXT NOT NULL DEFAULT 'todo' CHECK (status IN ('todo','done','dropped')),
    is_top3          INTEGER NOT NULL DEFAULT 0,
    rollover_count   INTEGER NOT NULL DEFAULT 0,
    estimated_min    INTEGER,
    actual_min       INTEGER,
    completed_at     TEXT,
    completed_date   TEXT,
    created_at       TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);
CREATE INDEX idx_task_planned ON task(planned_date, status);
CREATE INDEX idx_task_completed_date ON task(completed_date);
CREATE UNIQUE INDEX idx_task_recurring_day
    ON task(recurring_id, planned_date) WHERE recurring_id IS NOT NULL;

CREATE TABLE learning_session (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    learning_item_id INTEGER NOT NULL REFERENCES learning_item(id) ON DELETE CASCADE,
    task_id          INTEGER REFERENCES task(id) ON DELETE SET NULL,
    session_date     TEXT NOT NULL,
    duration_min     INTEGER NOT NULL CHECK (duration_min > 0),
    takeaway         TEXT NOT NULL,
    confidence       INTEGER CHECK (confidence BETWEEN 1 AND 5),
    created_at       TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);
CREATE INDEX idx_session_date ON learning_session(session_date);

CREATE TABLE daily_update (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    date              TEXT NOT NULL UNIQUE,
    planned_count     INTEGER NOT NULL DEFAULT 0,
    completed_count   INTEGER NOT NULL DEFAULT 0,
    completed_summary TEXT,
    learned_today     TEXT,
    study_minutes     INTEGER NOT NULL DEFAULT 0,
    day_rating        INTEGER CHECK (day_rating BETWEEN 1 AND 5),
    blockers          TEXT,
    tomorrow_focus    TEXT,
    created_at        TEXT NOT NULL DEFAULT (datetime('now','localtime')),
    updated_at        TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);

CREATE TABLE review (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    week_start  TEXT NOT NULL UNIQUE,
    wins        TEXT,
    blockers    TEXT,
    next_focus  TEXT,
    created_at  TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);
"""

# ---------------------------------------------------------------------------
# Migration registry — add new versions here
# ---------------------------------------------------------------------------
MIGRATIONS: dict[int, str] = {
    1: SCHEMA_V1_SQL,
    # 2: "ALTER TABLE task ADD COLUMN ...;",
}


def _get_current_version(conn: sqlite3.Connection) -> int:
    """Return the current schema version, or 0 if uninitialized."""
    try:
        row = conn.execute("SELECT version FROM schema_version").fetchone()
        return row[0] if row else 0
    except sqlite3.OperationalError:
        # schema_version table does not exist
        return 0


def run_migrations(conn: sqlite3.Connection) -> None:
    """Apply any unapplied migrations in ascending version order.

    Each migration's SQL is run inside a transaction. The schema_version
    row is updated after each successful migration.
    """
    current = _get_current_version(conn)
    for version in sorted(MIGRATIONS.keys()):
        if version <= current:
            continue
        conn.executescript(MIGRATIONS[version])
        # Version 1 already inserts the row; later versions update it
        if version > 1:
            conn.execute("UPDATE schema_version SET version = ?", (version,))
            conn.commit()
