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

SCHEMA_V2_SQL = """
-- 1. Create user table
CREATE TABLE IF NOT EXISTS user (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    email         TEXT NOT NULL UNIQUE COLLATE NOCASE,
    password_hash TEXT NOT NULL,
    name          TEXT,
    created_at    TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);

-- 2. Add user_id column to existing entity tables
ALTER TABLE goal ADD COLUMN user_id INTEGER REFERENCES user(id) ON DELETE CASCADE;
ALTER TABLE learning_item ADD COLUMN user_id INTEGER REFERENCES user(id) ON DELETE CASCADE;
ALTER TABLE recurring_task ADD COLUMN user_id INTEGER REFERENCES user(id) ON DELETE CASCADE;
ALTER TABLE task ADD COLUMN user_id INTEGER REFERENCES user(id) ON DELETE CASCADE;
ALTER TABLE learning_session ADD COLUMN user_id INTEGER REFERENCES user(id) ON DELETE CASCADE;

-- 3. Rebuild daily_update to have composite UNIQUE(user_id, date)
CREATE TABLE daily_update_v2 (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id           INTEGER REFERENCES user(id) ON DELETE CASCADE,
    date              TEXT NOT NULL,
    planned_count     INTEGER NOT NULL DEFAULT 0,
    completed_count   INTEGER NOT NULL DEFAULT 0,
    completed_summary TEXT,
    learned_today     TEXT,
    study_minutes     INTEGER NOT NULL DEFAULT 0,
    day_rating        INTEGER CHECK (day_rating BETWEEN 1 AND 5),
    blockers          TEXT,
    tomorrow_focus    TEXT,
    created_at        TEXT NOT NULL DEFAULT (datetime('now','localtime')),
    updated_at        TEXT NOT NULL DEFAULT (datetime('now','localtime')),
    UNIQUE(user_id, date)
);
INSERT INTO daily_update_v2 (id, user_id, date, planned_count, completed_count, completed_summary, learned_today, study_minutes, day_rating, blockers, tomorrow_focus, created_at, updated_at)
SELECT id, 1, date, planned_count, completed_count, completed_summary, learned_today, study_minutes, day_rating, blockers, tomorrow_focus, created_at, updated_at FROM daily_update;
DROP TABLE daily_update;
ALTER TABLE daily_update_v2 RENAME TO daily_update;

-- 4. Rebuild review to have composite UNIQUE(user_id, week_start)
CREATE TABLE review_v2 (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER REFERENCES user(id) ON DELETE CASCADE,
    week_start  TEXT NOT NULL,
    wins        TEXT,
    blockers    TEXT,
    next_focus  TEXT,
    created_at  TEXT NOT NULL DEFAULT (datetime('now','localtime')),
    UNIQUE(user_id, week_start)
);
INSERT INTO review_v2 (id, user_id, week_start, wins, blockers, next_focus, created_at)
SELECT id, 1, week_start, wins, blockers, next_focus, created_at FROM review;
DROP TABLE review;
ALTER TABLE review_v2 RENAME TO review;

-- 5. Indexes for fast user queries
CREATE INDEX IF NOT EXISTS idx_task_user ON task(user_id);
CREATE INDEX IF NOT EXISTS idx_task_user_planned ON task(user_id, planned_date, status);
CREATE INDEX IF NOT EXISTS idx_goal_user ON goal(user_id, status);
CREATE INDEX IF NOT EXISTS idx_learning_item_user ON learning_item(user_id, status);
CREATE INDEX IF NOT EXISTS idx_learning_session_user ON learning_session(user_id, session_date);
CREATE INDEX IF NOT EXISTS idx_recurring_user ON recurring_task(user_id, active);
CREATE INDEX IF NOT EXISTS idx_daily_update_user ON daily_update(user_id, date);
CREATE INDEX IF NOT EXISTS idx_review_user ON review(user_id, week_start);
"""

# ---------------------------------------------------------------------------
# Migration registry — add new versions here
# ---------------------------------------------------------------------------
MIGRATIONS: dict[int, str] = {
    1: SCHEMA_V1_SQL,
    2: SCHEMA_V2_SQL,
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
