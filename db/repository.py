"""All SQL operations live here.

UI code and services never write SQL directly — they call functions
from this module. Every function receives a connection from the caller.
"""

from __future__ import annotations

import sqlite3
from typing import Optional

from db.models import (
    Task, DailyUpdate, LearningItem, LearningSession,
    Goal, RecurringTask, Review,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _row_to_task(row: sqlite3.Row) -> Task:
    """Convert a sqlite3.Row to a Task dataclass."""
    return Task(**dict(row))


def _row_to_daily_update(row: sqlite3.Row) -> DailyUpdate:
    return DailyUpdate(**dict(row))


def _row_to_learning_item(row: sqlite3.Row) -> LearningItem:
    return LearningItem(**dict(row))


def _row_to_learning_session(row: sqlite3.Row) -> LearningSession:
    return LearningSession(**dict(row))


def _row_to_goal(row: sqlite3.Row) -> Goal:
    return Goal(**dict(row))


def _row_to_recurring_task(row: sqlite3.Row) -> RecurringTask:
    return RecurringTask(**dict(row))


def _row_to_review(row: sqlite3.Row) -> Review:
    return Review(**dict(row))


# ===================================================================
# TASK CRUD
# ===================================================================
def create_task(
    conn: sqlite3.Connection,
    title: str,
    planned_date: Optional[str] = None,
    due_date: Optional[str] = None,
    priority: str = "medium",
    category: str = "work",
    goal_id: Optional[int] = None,
    learning_item_id: Optional[int] = None,
    parent_task_id: Optional[int] = None,
    recurring_id: Optional[int] = None,
    estimated_min: Optional[int] = None,
    notes: Optional[str] = None,
) -> int:
    """Insert a new task and return its id."""
    cur = conn.execute(
        """INSERT INTO task
           (title, notes, planned_date, due_date, priority, category,
            goal_id, learning_item_id, parent_task_id, recurring_id, estimated_min)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (title, notes, planned_date, due_date, priority, category,
         goal_id, learning_item_id, parent_task_id, recurring_id, estimated_min),
    )
    conn.commit()
    return cur.lastrowid


def get_task(conn: sqlite3.Connection, task_id: int) -> Optional[Task]:
    """Return a single task by id, or None."""
    row = conn.execute("SELECT * FROM task WHERE id = ?", (task_id,)).fetchone()
    return _row_to_task(row) if row else None


def get_tasks_for_date(conn: sqlite3.Connection, date: str, status: Optional[str] = None) -> list[Task]:
    """Return tasks planned for a given date, optionally filtered by status."""
    if status:
        rows = conn.execute(
            "SELECT * FROM task WHERE planned_date = ? AND status = ? ORDER BY priority, title",
            (date, status),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM task WHERE planned_date = ? ORDER BY priority, title",
            (date,),
        ).fetchall()
    return [_row_to_task(r) for r in rows]


def get_todo_tasks_for_date(conn: sqlite3.Connection, date: str) -> list[Task]:
    """Return todo tasks planned for a given date."""
    return get_tasks_for_date(conn, date, status="todo")


def get_done_tasks_for_date(conn: sqlite3.Connection, date: str) -> list[Task]:
    """Return tasks completed on a given date (by completed_date)."""
    rows = conn.execute(
        "SELECT * FROM task WHERE completed_date = ? AND status = 'done' ORDER BY completed_at",
        (date,),
    ).fetchall()
    return [_row_to_task(r) for r in rows]


def get_top3_tasks(conn: sqlite3.Connection, date: str) -> list[Task]:
    """Return top-3 tasks for a given date."""
    rows = conn.execute(
        "SELECT * FROM task WHERE planned_date = ? AND is_top3 = 1 AND status = 'todo' ORDER BY priority",
        (date,),
    ).fetchall()
    return [_row_to_task(r) for r in rows]


def count_top3_todo(conn: sqlite3.Connection, date: str) -> int:
    """Count todo tasks flagged as top-3 for a date."""
    row = conn.execute(
        "SELECT COUNT(*) FROM task WHERE planned_date = ? AND is_top3 = 1 AND status = 'todo'",
        (date,),
    ).fetchone()
    return row[0]


def get_overdue_tasks(conn: sqlite3.Connection, today: str) -> list[Task]:
    """Return todo tasks with due_date before today."""
    rows = conn.execute(
        "SELECT * FROM task WHERE due_date < ? AND status = 'todo' ORDER BY due_date, priority",
        (today,),
    ).fetchall()
    return [_row_to_task(r) for r in rows]


def get_subtasks(conn: sqlite3.Connection, parent_id: int) -> list[Task]:
    """Return subtasks of a parent task."""
    rows = conn.execute(
        "SELECT * FROM task WHERE parent_task_id = ? ORDER BY created_at",
        (parent_id,),
    ).fetchall()
    return [_row_to_task(r) for r in rows]


def get_open_subtasks(conn: sqlite3.Connection, parent_id: int) -> list[Task]:
    """Return todo subtasks of a parent task."""
    rows = conn.execute(
        "SELECT * FROM task WHERE parent_task_id = ? AND status = 'todo' ORDER BY created_at",
        (parent_id,),
    ).fetchall()
    return [_row_to_task(r) for r in rows]


def get_backlog_tasks(conn: sqlite3.Connection) -> list[Task]:
    """Return todo tasks with no planned_date."""
    rows = conn.execute(
        "SELECT * FROM task WHERE planned_date IS NULL AND status = 'todo' ORDER BY priority, title",
    ).fetchall()
    return [_row_to_task(r) for r in rows]


def update_task(conn: sqlite3.Connection, task_id: int, **fields) -> None:
    """Update arbitrary fields on a task."""
    if not fields:
        return
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [task_id]
    conn.execute(f"UPDATE task SET {set_clause} WHERE id = ?", values)
    conn.commit()


def set_task_status(conn: sqlite3.Connection, task_id: int, status: str) -> None:
    """Set task status."""
    conn.execute("UPDATE task SET status = ? WHERE id = ?", (status, task_id))
    conn.commit()


def complete_task(conn: sqlite3.Connection, task_id: int, completed_at: str, completed_date: str) -> None:
    """Mark a task as done with timestamps."""
    conn.execute(
        "UPDATE task SET status = 'done', completed_at = ?, completed_date = ? WHERE id = ?",
        (completed_at, completed_date, task_id),
    )
    conn.commit()


def uncomplete_task(conn: sqlite3.Connection, task_id: int) -> None:
    """Revert a task to todo, clearing completion timestamps."""
    conn.execute(
        "UPDATE task SET status = 'todo', completed_at = NULL, completed_date = NULL WHERE id = ?",
        (task_id,),
    )
    conn.commit()


def drop_task(conn: sqlite3.Connection, task_id: int) -> None:
    """Soft-delete a task by setting status to dropped."""
    conn.execute("UPDATE task SET status = 'dropped' WHERE id = ?", (task_id,))
    conn.commit()


def restore_task(conn: sqlite3.Connection, task_id: int) -> None:
    """Restore a dropped task to todo."""
    conn.execute(
        "UPDATE task SET status = 'todo' WHERE id = ? AND status = 'dropped'",
        (task_id,),
    )
    conn.commit()


def delete_task_permanently(conn: sqlite3.Connection, task_id: int) -> None:
    """Permanently delete a task."""
    conn.execute("DELETE FROM task WHERE id = ?", (task_id,))
    conn.commit()


def set_top3(conn: sqlite3.Connection, task_id: int, value: int) -> None:
    """Set the is_top3 flag on a task."""
    conn.execute("UPDATE task SET is_top3 = ? WHERE id = ?", (value, task_id))
    conn.commit()


def rollover_tasks(conn: sqlite3.Connection, from_date: str, to_date: str) -> int:
    """Move todo tasks with planned_date <= from_date to to_date.

    Increments rollover_count by 1. Returns number moved.
    Does not touch backlog (NULL planned_date), done, or dropped tasks.
    """
    cur = conn.execute(
        """UPDATE task
           SET planned_date = ?, rollover_count = rollover_count + 1
           WHERE status = 'todo' AND planned_date IS NOT NULL AND planned_date <= ?""",
        (to_date, from_date),
    )
    conn.commit()
    return cur.rowcount


def get_tasks_for_goal_on_date(conn: sqlite3.Connection, goal_id: int, date: str) -> list[Task]:
    """Return tasks linked to a goal planned for a specific date."""
    rows = conn.execute(
        "SELECT * FROM task WHERE goal_id = ? AND planned_date = ? AND status = 'todo'",
        (goal_id, date),
    ).fetchall()
    return [_row_to_task(r) for r in rows]


def count_planned_for_date(conn: sqlite3.Connection, date: str) -> int:
    """Count tasks that were planned for a date (todo + done with completed_date == date)."""
    row = conn.execute(
        """SELECT COUNT(*) FROM task
           WHERE (planned_date = ? AND status = 'todo')
              OR (completed_date = ? AND status = 'done')""",
        (date, date),
    ).fetchone()
    return row[0]


def count_completed_for_date(conn: sqlite3.Connection, date: str) -> int:
    """Count tasks completed on a date."""
    row = conn.execute(
        "SELECT COUNT(*) FROM task WHERE completed_date = ? AND status = 'done'",
        (date,),
    ).fetchone()
    return row[0]


# ===================================================================
# DAILY UPDATE
# ===================================================================
def get_daily_update(conn: sqlite3.Connection, date: str) -> Optional[DailyUpdate]:
    """Return the daily update for a date, or None."""
    row = conn.execute("SELECT * FROM daily_update WHERE date = ?", (date,)).fetchone()
    return _row_to_daily_update(row) if row else None


def upsert_daily_update(
    conn: sqlite3.Connection,
    date: str,
    planned_count: int,
    completed_count: int,
    completed_summary: Optional[str] = None,
    learned_today: Optional[str] = None,
    study_minutes: int = 0,
    day_rating: Optional[int] = None,
    blockers: Optional[str] = None,
    tomorrow_focus: Optional[str] = None,
) -> int:
    """Insert or update a daily_update row. Returns the row id."""
    existing = get_daily_update(conn, date)
    if existing:
        conn.execute(
            """UPDATE daily_update
               SET planned_count = ?, completed_count = ?,
                   completed_summary = ?, learned_today = ?,
                   study_minutes = ?, day_rating = ?,
                   blockers = ?, tomorrow_focus = ?,
                   updated_at = datetime('now','localtime')
               WHERE date = ?""",
            (planned_count, completed_count, completed_summary, learned_today,
             study_minutes, day_rating, blockers, tomorrow_focus, date),
        )
        conn.commit()
        return existing.id
    else:
        cur = conn.execute(
            """INSERT INTO daily_update
               (date, planned_count, completed_count, completed_summary,
                learned_today, study_minutes, day_rating, blockers, tomorrow_focus)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (date, planned_count, completed_count, completed_summary,
             learned_today, study_minutes, day_rating, blockers, tomorrow_focus),
        )
        conn.commit()
        return cur.lastrowid


# ===================================================================
# LEARNING ITEM
# ===================================================================
def create_learning_item(
    conn: sqlite3.Connection,
    skill: str,
    resource: str,
    resource_type: str = "course",
    status: str = "in_progress",
    goal_id: Optional[int] = None,
) -> int:
    """Insert a learning item and return its id."""
    cur = conn.execute(
        """INSERT INTO learning_item (skill, resource, resource_type, status, goal_id)
           VALUES (?, ?, ?, ?, ?)""",
        (skill, resource, resource_type, status, goal_id),
    )
    conn.commit()
    return cur.lastrowid


def get_learning_item(conn: sqlite3.Connection, item_id: int) -> Optional[LearningItem]:
    row = conn.execute("SELECT * FROM learning_item WHERE id = ?", (item_id,)).fetchone()
    return _row_to_learning_item(row) if row else None


def get_all_learning_items(conn: sqlite3.Connection, status: Optional[str] = None) -> list[LearningItem]:
    if status:
        rows = conn.execute(
            "SELECT * FROM learning_item WHERE status = ? ORDER BY skill, resource", (status,)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM learning_item ORDER BY skill, resource"
        ).fetchall()
    return [_row_to_learning_item(r) for r in rows]


def update_learning_item(conn: sqlite3.Connection, item_id: int, **fields) -> None:
    if not fields:
        return
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [item_id]
    conn.execute(f"UPDATE learning_item SET {set_clause} WHERE id = ?", values)
    conn.commit()


# ===================================================================
# LEARNING SESSION
# ===================================================================
def create_learning_session(
    conn: sqlite3.Connection,
    learning_item_id: int,
    session_date: str,
    duration_min: int,
    takeaway: str,
    confidence: Optional[int] = None,
    task_id: Optional[int] = None,
) -> int:
    """Insert a learning session and return its id."""
    cur = conn.execute(
        """INSERT INTO learning_session
           (learning_item_id, task_id, session_date, duration_min, takeaway, confidence)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (learning_item_id, task_id, session_date, duration_min, takeaway, confidence),
    )
    conn.commit()
    return cur.lastrowid


def get_sessions_for_date(conn: sqlite3.Connection, date: str) -> list[LearningSession]:
    rows = conn.execute(
        "SELECT * FROM learning_session WHERE session_date = ? ORDER BY created_at",
        (date,),
    ).fetchall()
    return [_row_to_learning_session(r) for r in rows]


def get_sessions_for_item(conn: sqlite3.Connection, item_id: int) -> list[LearningSession]:
    rows = conn.execute(
        "SELECT * FROM learning_session WHERE learning_item_id = ? ORDER BY session_date DESC",
        (item_id,),
    ).fetchall()
    return [_row_to_learning_session(r) for r in rows]


def get_sessions_in_range(
    conn: sqlite3.Connection,
    start: str,
    end: str,
    skill: Optional[str] = None,
) -> list[LearningSession]:
    """Return sessions in a date range, optionally filtered by skill."""
    if skill:
        rows = conn.execute(
            """SELECT ls.* FROM learning_session ls
               JOIN learning_item li ON ls.learning_item_id = li.id
               WHERE ls.session_date BETWEEN ? AND ? AND li.skill = ?
               ORDER BY ls.session_date DESC""",
            (start, end, skill),
        ).fetchall()
    else:
        rows = conn.execute(
            """SELECT * FROM learning_session
               WHERE session_date BETWEEN ? AND ?
               ORDER BY session_date DESC""",
            (start, end),
        ).fetchall()
    return [_row_to_learning_session(r) for r in rows]


def search_takeaways(conn: sqlite3.Connection, query: str) -> list[LearningSession]:
    """Search sessions by takeaway text."""
    rows = conn.execute(
        "SELECT * FROM learning_session WHERE takeaway LIKE ? ORDER BY session_date DESC",
        (f"%{query}%",),
    ).fetchall()
    return [_row_to_learning_session(r) for r in rows]


def get_random_old_takeaways(conn: sqlite3.Connection, before_date: str, limit: int = 5) -> list[dict]:
    """Return random takeaways from before a given date for spaced repetition."""
    rows = conn.execute(
        """SELECT ls.takeaway, ls.session_date, li.skill, li.resource
           FROM learning_session ls
           JOIN learning_item li ON ls.learning_item_id = li.id
           WHERE ls.session_date < ?
           ORDER BY RANDOM() LIMIT ?""",
        (before_date, limit),
    ).fetchall()
    return [dict(r) for r in rows]


def study_minutes_for_date(conn: sqlite3.Connection, date: str) -> int:
    """Sum of session minutes for a date."""
    row = conn.execute(
        "SELECT COALESCE(SUM(duration_min), 0) FROM learning_session WHERE session_date = ?",
        (date,),
    ).fetchone()
    return row[0]


def study_minutes_for_goal(conn: sqlite3.Connection, goal_id: int, start: str, end: str) -> int:
    """Total session minutes for sessions linked to a goal's learning items, in a date range."""
    row = conn.execute(
        """SELECT COALESCE(SUM(ls.duration_min), 0)
           FROM learning_session ls
           JOIN learning_item li ON ls.learning_item_id = li.id
           WHERE li.goal_id = ? AND ls.session_date BETWEEN ? AND ?""",
        (goal_id, start, end),
    ).fetchone()
    return row[0]


def total_study_minutes_for_goal(conn: sqlite3.Connection, goal_id: int) -> int:
    """All-time session minutes for a goal."""
    row = conn.execute(
        """SELECT COALESCE(SUM(ls.duration_min), 0)
           FROM learning_session ls
           JOIN learning_item li ON ls.learning_item_id = li.id
           WHERE li.goal_id = ?""",
        (goal_id,),
    ).fetchone()
    return row[0]


def takeaways_for_date(conn: sqlite3.Connection, date: str) -> list[str]:
    """Return takeaway texts from sessions on a date."""
    rows = conn.execute(
        "SELECT takeaway FROM learning_session WHERE session_date = ? ORDER BY created_at",
        (date,),
    ).fetchall()
    return [r[0] for r in rows]


def get_distinct_skills(conn: sqlite3.Connection) -> list[str]:
    """Return distinct skill names."""
    rows = conn.execute(
        "SELECT DISTINCT skill FROM learning_item ORDER BY skill"
    ).fetchall()
    return [r[0] for r in rows]


# ===================================================================
# GOAL
# ===================================================================
def create_goal(
    conn: sqlite3.Connection,
    title: str,
    target_type: str,
    target_hours: float,
    start_date: str,
    target_date: Optional[str] = None,
) -> int:
    cur = conn.execute(
        """INSERT INTO goal (title, target_type, target_hours, start_date, target_date)
           VALUES (?, ?, ?, ?, ?)""",
        (title, target_type, target_hours, start_date, target_date),
    )
    conn.commit()
    return cur.lastrowid


def get_goal(conn: sqlite3.Connection, goal_id: int) -> Optional[Goal]:
    row = conn.execute("SELECT * FROM goal WHERE id = ?", (goal_id,)).fetchone()
    return _row_to_goal(row) if row else None


def get_active_goals(conn: sqlite3.Connection) -> list[Goal]:
    rows = conn.execute(
        "SELECT * FROM goal WHERE status = 'active' ORDER BY title"
    ).fetchall()
    return [_row_to_goal(r) for r in rows]


def get_all_goals(conn: sqlite3.Connection) -> list[Goal]:
    rows = conn.execute("SELECT * FROM goal ORDER BY status, title").fetchall()
    return [_row_to_goal(r) for r in rows]


def update_goal(conn: sqlite3.Connection, goal_id: int, **fields) -> None:
    if not fields:
        return
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [goal_id]
    conn.execute(f"UPDATE goal SET {set_clause} WHERE id = ?", values)
    conn.commit()


# ===================================================================
# RECURRING TASK
# ===================================================================
def create_recurring_task(
    conn: sqlite3.Connection,
    title: str,
    rule: str,
    start_date: str,
    priority: str = "medium",
    category: str = "work",
    goal_id: Optional[int] = None,
    learning_item_id: Optional[int] = None,
    estimated_min: Optional[int] = None,
    weekday: Optional[int] = None,
    day_of_month: Optional[int] = None,
    end_date: Optional[str] = None,
) -> int:
    cur = conn.execute(
        """INSERT INTO recurring_task
           (title, priority, category, goal_id, learning_item_id, estimated_min,
            rule, weekday, day_of_month, start_date, end_date)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (title, priority, category, goal_id, learning_item_id, estimated_min,
         rule, weekday, day_of_month, start_date, end_date),
    )
    conn.commit()
    return cur.lastrowid


def get_active_recurring_tasks(conn: sqlite3.Connection) -> list[RecurringTask]:
    rows = conn.execute(
        "SELECT * FROM recurring_task WHERE active = 1 ORDER BY title"
    ).fetchall()
    return [_row_to_recurring_task(r) for r in rows]


def get_all_recurring_tasks(conn: sqlite3.Connection) -> list[RecurringTask]:
    rows = conn.execute("SELECT * FROM recurring_task ORDER BY active DESC, title").fetchall()
    return [_row_to_recurring_task(r) for r in rows]


def update_recurring_task(conn: sqlite3.Connection, rec_id: int, **fields) -> None:
    if not fields:
        return
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [rec_id]
    conn.execute(f"UPDATE recurring_task SET {set_clause} WHERE id = ?", values)
    conn.commit()


def insert_recurring_task_instance(
    conn: sqlite3.Connection,
    recurring: RecurringTask,
    planned_date: str,
) -> bool:
    """Insert a task instance from a recurring template. Uses INSERT OR IGNORE
    for idempotency via the unique index. Returns True if inserted."""
    cur = conn.execute(
        """INSERT OR IGNORE INTO task
           (title, planned_date, priority, category, goal_id, learning_item_id,
            recurring_id, estimated_min)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (recurring.title, planned_date, recurring.priority, recurring.category,
         recurring.goal_id, recurring.learning_item_id, recurring.id,
         recurring.estimated_min),
    )
    conn.commit()
    return cur.rowcount > 0


# ===================================================================
# REVIEW
# ===================================================================
def get_review(conn: sqlite3.Connection, week_start: str) -> Optional[Review]:
    row = conn.execute("SELECT * FROM review WHERE week_start = ?", (week_start,)).fetchone()
    return _row_to_review(row) if row else None


def upsert_review(
    conn: sqlite3.Connection,
    week_start: str,
    wins: Optional[str] = None,
    blockers: Optional[str] = None,
    next_focus: Optional[str] = None,
) -> int:
    existing = get_review(conn, week_start)
    if existing:
        conn.execute(
            "UPDATE review SET wins = ?, blockers = ?, next_focus = ? WHERE week_start = ?",
            (wins, blockers, next_focus, week_start),
        )
        conn.commit()
        return existing.id
    else:
        cur = conn.execute(
            "INSERT INTO review (week_start, wins, blockers, next_focus) VALUES (?, ?, ?, ?)",
            (week_start, wins, blockers, next_focus),
        )
        conn.commit()
        return cur.lastrowid


def get_all_reviews(conn: sqlite3.Connection) -> list[Review]:
    rows = conn.execute("SELECT * FROM review ORDER BY week_start DESC").fetchall()
    return [_row_to_review(r) for r in rows]


# ===================================================================
# STATS QUERIES
# ===================================================================
def get_daily_updates_in_range(conn: sqlite3.Connection, start: str, end: str) -> list[DailyUpdate]:
    rows = conn.execute(
        "SELECT * FROM daily_update WHERE date BETWEEN ? AND ? ORDER BY date",
        (start, end),
    ).fetchall()
    return [_row_to_daily_update(r) for r in rows]


def get_all_update_dates(conn: sqlite3.Connection) -> list[str]:
    """Return all dates that have a daily update, ordered ascending."""
    rows = conn.execute("SELECT date FROM daily_update ORDER BY date").fetchall()
    return [r[0] for r in rows]


def get_done_tasks_in_range(conn: sqlite3.Connection, start: str, end: str) -> list[Task]:
    """Return tasks completed in a date range."""
    rows = conn.execute(
        "SELECT * FROM task WHERE completed_date BETWEEN ? AND ? AND status = 'done' ORDER BY completed_date",
        (start, end),
    ).fetchall()
    return [_row_to_task(r) for r in rows]


def count_done_tasks_in_range(conn: sqlite3.Connection, start: str, end: str) -> int:
    row = conn.execute(
        "SELECT COUNT(*) FROM task WHERE completed_date BETWEEN ? AND ? AND status = 'done'",
        (start, end),
    ).fetchone()
    return row[0]


def get_all_table_names(conn: sqlite3.Connection) -> list[str]:
    """Return all user table names (excluding sqlite internals)."""
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
    ).fetchall()
    return [r[0] for r in rows]


def export_table_as_dicts(conn: sqlite3.Connection, table_name: str) -> list[dict]:
    """Return all rows of a table as dicts."""
    rows = conn.execute(f"SELECT * FROM {table_name}").fetchall()
    return [dict(r) for r in rows]
