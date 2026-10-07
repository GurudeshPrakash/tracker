"""All SQL operations live here.

UI code and services never write SQL directly — they call functions
from this module. Every function receives a connection from the caller.
Supports optional user_id scoping for complete multi-tenant isolation.
"""

from __future__ import annotations

import sqlite3
from typing import Optional

from db.models import (
    Task, DailyUpdate, LearningItem, LearningSession,
    Goal, RecurringTask, Review, User,
)


# ---------------------------------------------------------------------------
# Query & Filter Constants
# ---------------------------------------------------------------------------
SQL_PLANNED_DATE = "planned_date = ?"
SQL_USER_ID = "user_id = ?"
SQL_STATUS_DONE = "status = 'done'"
SQL_STATUS_TODO = "status = 'todo'"
SQL_WHERE_ID = "WHERE id = ?"
SQL_AND_USER_ID = " AND user_id = ?"
SQL_SESSION_DATE = "session_date = ?"
SQL_LS_USER_ID = "ls.user_id = ?"
SQL_WHERE_USER_ID = "WHERE user_id = ?"



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
    user_id: Optional[int] = None,
) -> int:
    """Insert a new task and return its id."""
    cur = conn.execute(
        """INSERT INTO task
           (title, notes, planned_date, due_date, priority, category,
            goal_id, learning_item_id, parent_task_id, recurring_id, estimated_min, user_id)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (title, notes, planned_date, due_date, priority, category,
         goal_id, learning_item_id, parent_task_id, recurring_id, estimated_min, user_id),
    )
    conn.commit()
    return cur.lastrowid


def get_task(conn: sqlite3.Connection, task_id: int, user_id: Optional[int] = None) -> Optional[Task]:
    """Return a single task by id, or None."""
    if user_id is not None:
        row = conn.execute("SELECT * FROM task WHERE id = ? AND user_id = ?", (task_id, user_id)).fetchone()
    else:
        row = conn.execute("SELECT * FROM task WHERE id = ?", (task_id,)).fetchone()
    return _row_to_task(row) if row else None


def get_tasks_for_date(
    conn: sqlite3.Connection,
    date: str,
    status: Optional[str] = None,
    user_id: Optional[int] = None,
) -> list[Task]:
    """Return tasks planned for a given date, optionally filtered by status and user."""
    clauses = [SQL_PLANNED_DATE]
    params: list[object] = [date]
    if status:
        clauses.append("status = ?")
        params.append(status)
    if user_id is not None:
        clauses.append(SQL_USER_ID)
        params.append(user_id)

    sql = f"SELECT * FROM task WHERE {' AND '.join(clauses)} ORDER BY priority, title"
    rows = conn.execute(sql, params).fetchall()
    return [_row_to_task(r) for r in rows]


def get_todo_tasks_for_date(conn: sqlite3.Connection, date: str, user_id: Optional[int] = None) -> list[Task]:
    """Return todo tasks planned for a given date."""
    return get_tasks_for_date(conn, date, status="todo", user_id=user_id)


def get_done_tasks_for_date(conn: sqlite3.Connection, date: str, user_id: Optional[int] = None) -> list[Task]:
    """Return tasks completed on a given date (by completed_date)."""
    clauses = ["completed_date = ?", SQL_STATUS_DONE]
    params: list[object] = [date]
    if user_id is not None:
        clauses.append(SQL_USER_ID)
        params.append(user_id)
    sql = f"SELECT * FROM task WHERE {' AND '.join(clauses)} ORDER BY completed_at"
    rows = conn.execute(sql, params).fetchall()
    return [_row_to_task(r) for r in rows]


def get_top3_tasks(conn: sqlite3.Connection, date: str, user_id: Optional[int] = None) -> list[Task]:
    """Return top-3 tasks for a given date."""
    clauses = [SQL_PLANNED_DATE, "is_top3 = 1", SQL_STATUS_TODO]
    params: list[object] = [date]
    if user_id is not None:
        clauses.append(SQL_USER_ID)
        params.append(user_id)
    sql = f"SELECT * FROM task WHERE {' AND '.join(clauses)} ORDER BY priority"
    rows = conn.execute(sql, params).fetchall()
    return [_row_to_task(r) for r in rows]


def count_top3_todo(conn: sqlite3.Connection, date: str, user_id: Optional[int] = None) -> int:
    """Count todo tasks flagged as top-3 for a date."""
    clauses = [SQL_PLANNED_DATE, "is_top3 = 1", SQL_STATUS_TODO]
    params: list[object] = [date]
    if user_id is not None:
        clauses.append(SQL_USER_ID)
        params.append(user_id)
    sql = f"SELECT COUNT(*) FROM task WHERE {' AND '.join(clauses)}"
    row = conn.execute(sql, params).fetchone()
    return row[0] if row else 0


def get_overdue_tasks(conn: sqlite3.Connection, today: str, user_id: Optional[int] = None) -> list[Task]:
    """Return todo tasks with due_date before today."""
    clauses = ["due_date < ?", SQL_STATUS_TODO]
    params: list[object] = [today]
    if user_id is not None:
        clauses.append(SQL_USER_ID)
        params.append(user_id)
    sql = f"SELECT * FROM task WHERE {' AND '.join(clauses)} ORDER BY due_date, priority"
    rows = conn.execute(sql, params).fetchall()
    return [_row_to_task(r) for r in rows]


def get_subtasks(conn: sqlite3.Connection, parent_id: int, user_id: Optional[int] = None) -> list[Task]:
    """Return subtasks of a parent task."""
    clauses = ["parent_task_id = ?"]
    params: list[object] = [parent_id]
    if user_id is not None:
        clauses.append(SQL_USER_ID)
        params.append(user_id)
    sql = f"SELECT * FROM task WHERE {' AND '.join(clauses)} ORDER BY created_at"
    rows = conn.execute(sql, params).fetchall()
    return [_row_to_task(r) for r in rows]


def get_open_subtasks(conn: sqlite3.Connection, parent_id: int, user_id: Optional[int] = None) -> list[Task]:
    """Return todo subtasks of a parent task."""
    clauses = ["parent_task_id = ?", SQL_STATUS_TODO]
    params: list[object] = [parent_id]
    if user_id is not None:
        clauses.append(SQL_USER_ID)
        params.append(user_id)
    sql = f"SELECT * FROM task WHERE {' AND '.join(clauses)} ORDER BY created_at"
    rows = conn.execute(sql, params).fetchall()
    return [_row_to_task(r) for r in rows]


def get_backlog_tasks(conn: sqlite3.Connection, user_id: Optional[int] = None) -> list[Task]:
    """Return todo tasks with no planned_date."""
    clauses = ["planned_date IS NULL", SQL_STATUS_TODO]
    params: list[object] = []
    if user_id is not None:
        clauses.append(SQL_USER_ID)
        params.append(user_id)
    sql = f"SELECT * FROM task WHERE {' AND '.join(clauses)} ORDER BY priority, title"
    rows = conn.execute(sql, params).fetchall()
    return [_row_to_task(r) for r in rows]


def update_task(conn: sqlite3.Connection, task_id: int, user_id: Optional[int] = None, **fields) -> None:
    """Update arbitrary fields on a task."""
    if not fields:
        return
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [task_id]
    where = SQL_WHERE_ID
    if user_id is not None:
        where += SQL_AND_USER_ID
        values.append(user_id)
    conn.execute(f"UPDATE task SET {set_clause} {where}", values)
    conn.commit()


def set_task_status(conn: sqlite3.Connection, task_id: int, status: str, user_id: Optional[int] = None) -> None:
    """Set task status."""
    where = SQL_WHERE_ID
    params: list[object] = [status, task_id]
    if user_id is not None:
        where += SQL_AND_USER_ID
        params.append(user_id)
    conn.execute(f"UPDATE task SET status = ? {where}", params)
    conn.commit()


def complete_task(
    conn: sqlite3.Connection,
    task_id: int,
    completed_at: str,
    completed_date: str,
    user_id: Optional[int] = None,
) -> None:
    """Mark a task as done with timestamps."""
    where = SQL_WHERE_ID
    params: list[object] = [completed_at, completed_date, task_id]
    if user_id is not None:
        where += SQL_AND_USER_ID
        params.append(user_id)
    conn.execute(
        f"UPDATE task SET status = 'done', completed_at = ?, completed_date = ? {where}",
        params,
    )
    conn.commit()


def uncomplete_task(conn: sqlite3.Connection, task_id: int, user_id: Optional[int] = None) -> None:
    """Revert a task to todo, clearing completion timestamps."""
    where = SQL_WHERE_ID
    params: list[object] = [task_id]
    if user_id is not None:
        where += SQL_AND_USER_ID
        params.append(user_id)
    conn.execute(
        f"UPDATE task SET status = 'todo', completed_at = NULL, completed_date = NULL {where}",
        params,
    )
    conn.commit()


def drop_task(conn: sqlite3.Connection, task_id: int, user_id: Optional[int] = None) -> None:
    """Soft-delete a task by setting status to dropped."""
    where = SQL_WHERE_ID
    params: list[object] = [task_id]
    if user_id is not None:
        where += SQL_AND_USER_ID
        params.append(user_id)
    conn.execute(f"UPDATE task SET status = 'dropped' {where}", params)
    conn.commit()


def restore_task(conn: sqlite3.Connection, task_id: int, user_id: Optional[int] = None) -> None:
    """Restore a dropped task to todo."""
    where = "WHERE id = ? AND status = 'dropped'"
    params: list[object] = [task_id]
    if user_id is not None:
        where += SQL_AND_USER_ID
        params.append(user_id)
    conn.execute(f"UPDATE task SET status = 'todo' {where}", params)
    conn.commit()


def delete_task_permanently(conn: sqlite3.Connection, task_id: int, user_id: Optional[int] = None) -> None:
    """Permanently delete a task."""
    where = SQL_WHERE_ID
    params: list[object] = [task_id]
    if user_id is not None:
        where += SQL_AND_USER_ID
        params.append(user_id)
    conn.execute(f"DELETE FROM task {where}", params)
    conn.commit()


def set_top3(conn: sqlite3.Connection, task_id: int, value: int, user_id: Optional[int] = None) -> None:
    """Set the is_top3 flag on a task."""
    where = SQL_WHERE_ID
    params: list[object] = [value, task_id]
    if user_id is not None:
        where += SQL_AND_USER_ID
        params.append(user_id)
    conn.execute(f"UPDATE task SET is_top3 = ? {where}", params)
    conn.commit()


def rollover_tasks(
    conn: sqlite3.Connection,
    from_date: str,
    to_date: str,
    user_id: Optional[int] = None,
) -> int:
    """Move todo tasks with planned_date <= from_date to to_date.

    Increments rollover_count by 1. Returns number moved.
    Does not touch backlog (NULL planned_date), done, or dropped tasks.
    """
    where = "status = 'todo' AND planned_date IS NOT NULL AND planned_date <= ?"
    params: list[object] = [to_date, from_date]
    if user_id is not None:
        where += SQL_AND_USER_ID
        params.append(user_id)

    cur = conn.execute(
        f"""UPDATE task
            SET planned_date = ?, rollover_count = rollover_count + 1
            WHERE {where}""",
        params,
    )
    conn.commit()
    return cur.rowcount


def get_tasks_for_goal_on_date(
    conn: sqlite3.Connection,
    goal_id: int,
    date: str,
    user_id: Optional[int] = None,
) -> list[Task]:
    """Return tasks linked to a goal planned for a specific date."""
    clauses = ["goal_id = ?", SQL_PLANNED_DATE, SQL_STATUS_TODO]
    params: list[object] = [goal_id, date]
    if user_id is not None:
        clauses.append(SQL_USER_ID)
        params.append(user_id)
    sql = f"SELECT * FROM task WHERE {' AND '.join(clauses)}"
    rows = conn.execute(sql, params).fetchall()
    return [_row_to_task(r) for r in rows]


def count_planned_for_date(conn: sqlite3.Connection, date: str, user_id: Optional[int] = None) -> int:
    """Count tasks that were planned for a date (todo + done with completed_date == date)."""
    clauses = [
        "((planned_date = ? AND status = 'todo') OR (completed_date = ? AND status = 'done'))"
    ]
    params: list[object] = [date, date]
    if user_id is not None:
        clauses.append(SQL_USER_ID)
        params.append(user_id)
    sql = f"SELECT COUNT(*) FROM task WHERE {' AND '.join(clauses)}"
    row = conn.execute(sql, params).fetchone()
    return row[0] if row else 0


def count_completed_for_date(conn: sqlite3.Connection, date: str, user_id: Optional[int] = None) -> int:
    """Count tasks completed on a date."""
    clauses = ["completed_date = ?", SQL_STATUS_DONE]
    params: list[object] = [date]
    if user_id is not None:
        clauses.append(SQL_USER_ID)
        params.append(user_id)
    sql = f"SELECT COUNT(*) FROM task WHERE {' AND '.join(clauses)}"
    row = conn.execute(sql, params).fetchone()
    return row[0] if row else 0


# ===================================================================
# DAILY UPDATE
# ===================================================================
def get_daily_update(conn: sqlite3.Connection, date: str, user_id: Optional[int] = None) -> Optional[DailyUpdate]:
    """Return the daily update for a date, or None."""
    if user_id is not None:
        row = conn.execute("SELECT * FROM daily_update WHERE date = ? AND user_id = ?", (date, user_id)).fetchone()
    else:
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
    user_id: Optional[int] = None,
) -> int:
    """Insert or update a daily_update row. Returns the row id."""
    existing = get_daily_update(conn, date, user_id=user_id)
    if existing:
        conn.execute(
            """UPDATE daily_update
               SET planned_count = ?, completed_count = ?,
                   completed_summary = ?, learned_today = ?,
                   study_minutes = ?, day_rating = ?,
                   blockers = ?, tomorrow_focus = ?,
                   updated_at = datetime('now','localtime')
               WHERE id = ?""",
            (planned_count, completed_count, completed_summary, learned_today,
             study_minutes, day_rating, blockers, tomorrow_focus, existing.id),
        )
        conn.commit()
        return existing.id
    else:
        cur = conn.execute(
            """INSERT INTO daily_update
               (date, planned_count, completed_count, completed_summary,
                learned_today, study_minutes, day_rating, blockers, tomorrow_focus, user_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (date, planned_count, completed_count, completed_summary,
             learned_today, study_minutes, day_rating, blockers, tomorrow_focus, user_id),
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
    user_id: Optional[int] = None,
) -> int:
    """Insert a learning item and return its id."""
    cur = conn.execute(
        """INSERT INTO learning_item (skill, resource, resource_type, status, goal_id, user_id)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (skill, resource, resource_type, status, goal_id, user_id),
    )
    conn.commit()
    return cur.lastrowid


def get_learning_item(conn: sqlite3.Connection, item_id: int, user_id: Optional[int] = None) -> Optional[LearningItem]:
    if user_id is not None:
        row = conn.execute("SELECT * FROM learning_item WHERE id = ? AND user_id = ?", (item_id, user_id)).fetchone()
    else:
        row = conn.execute("SELECT * FROM learning_item WHERE id = ?", (item_id,)).fetchone()
    return _row_to_learning_item(row) if row else None


def get_all_learning_items(
    conn: sqlite3.Connection,
    status: Optional[str] = None,
    user_id: Optional[int] = None,
) -> list[LearningItem]:
    clauses = []
    params: list[object] = []
    if status:
        clauses.append("status = ?")
        params.append(status)
    if user_id is not None:
        clauses.append(SQL_USER_ID)
        params.append(user_id)

    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    sql = f"SELECT * FROM learning_item {where} ORDER BY skill, resource"
    rows = conn.execute(sql, params).fetchall()
    return [_row_to_learning_item(r) for r in rows]


def update_learning_item(conn: sqlite3.Connection, item_id: int, user_id: Optional[int] = None, **fields) -> None:
    if not fields:
        return
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [item_id]
    where = SQL_WHERE_ID
    if user_id is not None:
        where += SQL_AND_USER_ID
        values.append(user_id)
    conn.execute(f"UPDATE learning_item SET {set_clause} {where}", values)
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
    user_id: Optional[int] = None,
) -> int:
    """Insert a learning session and return its id."""
    cur = conn.execute(
        """INSERT INTO learning_session
           (learning_item_id, task_id, session_date, duration_min, takeaway, confidence, user_id)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (learning_item_id, task_id, session_date, duration_min, takeaway, confidence, user_id),
    )
    conn.commit()
    return cur.lastrowid


def get_sessions_for_date(conn: sqlite3.Connection, date: str, user_id: Optional[int] = None) -> list[LearningSession]:
    clauses = [SQL_SESSION_DATE]
    params: list[object] = [date]
    if user_id is not None:
        clauses.append(SQL_USER_ID)
        params.append(user_id)
    sql = f"SELECT * FROM learning_session WHERE {' AND '.join(clauses)} ORDER BY created_at"
    rows = conn.execute(sql, params).fetchall()
    return [_row_to_learning_session(r) for r in rows]


def get_sessions_for_item(conn: sqlite3.Connection, item_id: int, user_id: Optional[int] = None) -> list[LearningSession]:
    clauses = ["learning_item_id = ?"]
    params: list[object] = [item_id]
    if user_id is not None:
        clauses.append(SQL_USER_ID)
        params.append(user_id)
    sql = f"SELECT * FROM learning_session WHERE {' AND '.join(clauses)} ORDER BY session_date DESC"
    rows = conn.execute(sql, params).fetchall()
    return [_row_to_learning_session(r) for r in rows]


def get_sessions_in_range(
    conn: sqlite3.Connection,
    start: str,
    end: str,
    skill: Optional[str] = None,
    user_id: Optional[int] = None,
) -> list[LearningSession]:
    """Return sessions in a date range, optionally filtered by skill and user."""
    clauses = ["ls.session_date BETWEEN ? AND ?"]
    params: list[object] = [start, end]
    if user_id is not None:
        clauses.append(SQL_LS_USER_ID)
        params.append(user_id)

    if skill:
        clauses.append("li.skill = ?")
        params.append(skill)
        sql = f"""SELECT ls.* FROM learning_session ls
                  JOIN learning_item li ON ls.learning_item_id = li.id
                  WHERE {' AND '.join(clauses)}
                  ORDER BY ls.session_date DESC"""
    else:
        sql = f"""SELECT ls.* FROM learning_session ls
                  WHERE {' AND '.join(clauses)}
                  ORDER BY ls.session_date DESC"""

    rows = conn.execute(sql, params).fetchall()
    return [_row_to_learning_session(r) for r in rows]


def search_takeaways(conn: sqlite3.Connection, query: str, user_id: Optional[int] = None) -> list[LearningSession]:
    """Search sessions by takeaway text."""
    clauses = ["takeaway LIKE ?"]
    params: list[object] = [f"%{query}%"]
    if user_id is not None:
        clauses.append(SQL_USER_ID)
        params.append(user_id)
    sql = f"SELECT * FROM learning_session WHERE {' AND '.join(clauses)} ORDER BY session_date DESC"
    rows = conn.execute(sql, params).fetchall()
    return [_row_to_learning_session(r) for r in rows]


def get_random_old_takeaways(
    conn: sqlite3.Connection,
    before_date: str,
    limit: int = 5,
    user_id: Optional[int] = None,
) -> list[dict]:
    """Return random takeaways from before a given date for spaced repetition."""
    clauses = ["ls.session_date < ?"]
    params: list[object] = [before_date]
    if user_id is not None:
        clauses.append(SQL_LS_USER_ID)
        params.append(user_id)
    params.append(limit)

    sql = f"""SELECT ls.takeaway, ls.session_date, li.skill, li.resource
              FROM learning_session ls
              JOIN learning_item li ON ls.learning_item_id = li.id
              WHERE {' AND '.join(clauses)}
              ORDER BY RANDOM() LIMIT ?"""
    rows = conn.execute(sql, params).fetchall()
    return [
        {
            "takeaway": r["takeaway"],
            "session_date": r["session_date"],
            "skill": r["skill"],
            "resource": r["resource"],
        }
        for r in rows
    ]


def study_minutes_for_date(conn: sqlite3.Connection, date: str, user_id: Optional[int] = None) -> int:
    """Sum duration_min of learning sessions on a given date."""
    clauses = [SQL_SESSION_DATE]
    params: list[object] = [date]
    if user_id is not None:
        clauses.append(SQL_USER_ID)
        params.append(user_id)
    sql = f"SELECT COALESCE(SUM(duration_min), 0) FROM learning_session WHERE {' AND '.join(clauses)}"
    row = conn.execute(sql, params).fetchone()
    return row[0] if row else 0


def study_minutes_for_goal(
    conn: sqlite3.Connection,
    goal_id: int,
    start: str,
    end: str,
    user_id: Optional[int] = None,
) -> int:
    """Sum duration_min for sessions linked to items belonging to goal_id in date range."""
    clauses = [
        "ls.session_date BETWEEN ? AND ?",
        "ls.learning_item_id IN (SELECT id FROM learning_item WHERE goal_id = ?)"
    ]
    params: list[object] = [start, end, goal_id]
    if user_id is not None:
        clauses.append(SQL_LS_USER_ID)
        params.append(user_id)
    sql = f"SELECT COALESCE(SUM(ls.duration_min), 0) FROM learning_session ls WHERE {' AND '.join(clauses)}"
    row = conn.execute(sql, params).fetchone()
    return row[0] if row else 0


def total_study_minutes_for_goal(conn: sqlite3.Connection, goal_id: int, user_id: Optional[int] = None) -> int:
    """Sum all duration_min for sessions linked to items belonging to goal_id."""
    clauses = [
        "learning_item_id IN (SELECT id FROM learning_item WHERE goal_id = ?)"
    ]
    params: list[object] = [goal_id]
    if user_id is not None:
        clauses.append(SQL_USER_ID)
        params.append(user_id)
    sql = f"SELECT COALESCE(SUM(duration_min), 0) FROM learning_session WHERE {' AND '.join(clauses)}"
    row = conn.execute(sql, params).fetchone()
    return row[0] if row else 0


def takeaways_for_date(conn: sqlite3.Connection, date: str, user_id: Optional[int] = None) -> list[str]:
    """Return all takeaways logged on a given date."""
    clauses = [SQL_SESSION_DATE]
    params: list[object] = [date]
    if user_id is not None:
        clauses.append(SQL_USER_ID)
        params.append(user_id)
    sql = f"SELECT takeaway FROM learning_session WHERE {' AND '.join(clauses)} ORDER BY created_at"
    rows = conn.execute(sql, params).fetchall()
    return [r[0] for r in rows]


def get_distinct_skills(conn: sqlite3.Connection, user_id: Optional[int] = None) -> list[str]:
    """Return sorted distinct skill names from learning_item."""
    where = SQL_WHERE_USER_ID if user_id is not None else ""
    params = [user_id] if user_id is not None else []
    rows = conn.execute(f"SELECT DISTINCT skill FROM learning_item {where} ORDER BY skill", params).fetchall()
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
    status: str = "active",
    user_id: Optional[int] = None,
) -> int:
    cur = conn.execute(
        """INSERT INTO goal (title, target_type, target_hours, start_date, target_date, status, user_id)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (title, target_type, target_hours, start_date, target_date, status, user_id),
    )
    conn.commit()
    return cur.lastrowid


def get_goal(conn: sqlite3.Connection, goal_id: int, user_id: Optional[int] = None) -> Optional[Goal]:
    if user_id is not None:
        row = conn.execute("SELECT * FROM goal WHERE id = ? AND user_id = ?", (goal_id, user_id)).fetchone()
    else:
        row = conn.execute("SELECT * FROM goal WHERE id = ?", (goal_id,)).fetchone()
    return _row_to_goal(row) if row else None


def get_active_goals(conn: sqlite3.Connection, user_id: Optional[int] = None) -> list[Goal]:
    where = "WHERE status = 'active'"
    params: list[object] = []
    if user_id is not None:
        where += SQL_AND_USER_ID
        params.append(user_id)
    rows = conn.execute(f"SELECT * FROM goal {where} ORDER BY title", params).fetchall()
    return [_row_to_goal(r) for r in rows]


def get_all_goals(conn: sqlite3.Connection, user_id: Optional[int] = None) -> list[Goal]:
    where = SQL_WHERE_USER_ID if user_id is not None else ""
    params = [user_id] if user_id is not None else []
    rows = conn.execute(f"SELECT * FROM goal {where} ORDER BY status, title", params).fetchall()
    return [_row_to_goal(r) for r in rows]


def update_goal(conn: sqlite3.Connection, goal_id: int, user_id: Optional[int] = None, **fields) -> None:
    if not fields:
        return
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [goal_id]
    where = SQL_WHERE_ID
    if user_id is not None:
        where += SQL_AND_USER_ID
        values.append(user_id)
    conn.execute(f"UPDATE goal SET {set_clause} {where}", values)
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
    user_id: Optional[int] = None,
) -> int:
    cur = conn.execute(
        """INSERT INTO recurring_task
           (title, priority, category, goal_id, learning_item_id, estimated_min,
            rule, weekday, day_of_month, start_date, end_date, user_id)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (title, priority, category, goal_id, learning_item_id, estimated_min,
         rule, weekday, day_of_month, start_date, end_date, user_id),
    )
    conn.commit()
    return cur.lastrowid


def get_active_recurring_tasks(conn: sqlite3.Connection, user_id: Optional[int] = None) -> list[RecurringTask]:
    where = "WHERE active = 1"
    params: list[object] = []
    if user_id is not None:
        where += SQL_AND_USER_ID
        params.append(user_id)
    rows = conn.execute(f"SELECT * FROM recurring_task {where} ORDER BY title", params).fetchall()
    return [_row_to_recurring_task(r) for r in rows]


def get_all_recurring_tasks(conn: sqlite3.Connection, user_id: Optional[int] = None) -> list[RecurringTask]:
    where = SQL_WHERE_USER_ID if user_id is not None else ""
    params = [user_id] if user_id is not None else []
    rows = conn.execute(f"SELECT * FROM recurring_task {where} ORDER BY active DESC, title", params).fetchall()
    return [_row_to_recurring_task(r) for r in rows]


def update_recurring_task(conn: sqlite3.Connection, rec_id: int, user_id: Optional[int] = None, **fields) -> None:
    if not fields:
        return
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [rec_id]
    where = SQL_WHERE_ID
    if user_id is not None:
        where += SQL_AND_USER_ID
        values.append(user_id)
    conn.execute(f"UPDATE recurring_task SET {set_clause} {where}", values)
    conn.commit()


def delete_recurring_task(conn: sqlite3.Connection, rec_id: int, user_id: Optional[int] = None) -> None:
    where = SQL_WHERE_ID
    params: list[object] = [rec_id]
    if user_id is not None:
        where += SQL_AND_USER_ID
        params.append(user_id)
    conn.execute(f"DELETE FROM recurring_task {where}", params)
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
            recurring_id, estimated_min, user_id)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (recurring.title, planned_date, recurring.priority, recurring.category,
         recurring.goal_id, recurring.learning_item_id, recurring.id,
         recurring.estimated_min, recurring.user_id),
    )
    conn.commit()
    return cur.rowcount > 0


# ===================================================================
# REVIEW
# ===================================================================
def get_review(conn: sqlite3.Connection, week_start: str, user_id: Optional[int] = None) -> Optional[Review]:
    if user_id is not None:
        row = conn.execute("SELECT * FROM review WHERE week_start = ? AND user_id = ?", (week_start, user_id)).fetchone()
    else:
        row = conn.execute("SELECT * FROM review WHERE week_start = ?", (week_start,)).fetchone()
    return _row_to_review(row) if row else None


def upsert_review(
    conn: sqlite3.Connection,
    week_start: str,
    wins: Optional[str] = None,
    blockers: Optional[str] = None,
    next_focus: Optional[str] = None,
    user_id: Optional[int] = None,
) -> int:
    existing = get_review(conn, week_start, user_id=user_id)
    if existing:
        conn.execute(
            "UPDATE review SET wins = ?, blockers = ?, next_focus = ? WHERE id = ?",
            (wins, blockers, next_focus, existing.id),
        )
        conn.commit()
        return existing.id
    else:
        cur = conn.execute(
            "INSERT INTO review (week_start, wins, blockers, next_focus, user_id) VALUES (?, ?, ?, ?, ?)",
            (week_start, wins, blockers, next_focus, user_id),
        )
        conn.commit()
        return cur.lastrowid


def get_all_reviews(conn: sqlite3.Connection, user_id: Optional[int] = None) -> list[Review]:
    where = SQL_WHERE_USER_ID if user_id is not None else ""
    params = [user_id] if user_id is not None else []
    rows = conn.execute(f"SELECT * FROM review {where} ORDER BY week_start DESC", params).fetchall()
    return [_row_to_review(r) for r in rows]


# ===================================================================
# STATS QUERIES
# ===================================================================
def get_daily_updates_in_range(
    conn: sqlite3.Connection,
    start: str,
    end: str,
    user_id: Optional[int] = None,
) -> list[DailyUpdate]:
    clauses = ["date BETWEEN ? AND ?"]
    params: list[object] = [start, end]
    if user_id is not None:
        clauses.append(SQL_USER_ID)
        params.append(user_id)
    sql = f"SELECT * FROM daily_update WHERE {' AND '.join(clauses)} ORDER BY date"
    rows = conn.execute(sql, params).fetchall()
    return [_row_to_daily_update(r) for r in rows]


def get_all_update_dates(conn: sqlite3.Connection, user_id: Optional[int] = None) -> list[str]:
    """Return all dates that have a daily update, ordered ascending."""
    where = SQL_WHERE_USER_ID if user_id is not None else ""
    params = [user_id] if user_id is not None else []
    rows = conn.execute(f"SELECT date FROM daily_update {where} ORDER BY date", params).fetchall()
    return [r[0] for r in rows]


def get_done_tasks_in_range(
    conn: sqlite3.Connection,
    start: str,
    end: str,
    user_id: Optional[int] = None,
) -> list[Task]:
    """Return tasks completed in a date range."""
    clauses = ["completed_date BETWEEN ? AND ?", SQL_STATUS_DONE]
    params: list[object] = [start, end]
    if user_id is not None:
        clauses.append(SQL_USER_ID)
        params.append(user_id)
    sql = f"SELECT * FROM task WHERE {' AND '.join(clauses)} ORDER BY completed_date"
    rows = conn.execute(sql, params).fetchall()
    return [_row_to_task(r) for r in rows]


def count_done_tasks_in_range(
    conn: sqlite3.Connection,
    start: str,
    end: str,
    user_id: Optional[int] = None,
) -> int:
    clauses = ["completed_date BETWEEN ? AND ?", SQL_STATUS_DONE]
    params: list[object] = [start, end]
    if user_id is not None:
        clauses.append(SQL_USER_ID)
        params.append(user_id)
    sql = f"SELECT COUNT(*) FROM task WHERE {' AND '.join(clauses)}"
    row = conn.execute(sql, params).fetchone()
    return row[0] if row else 0


def get_all_table_names(conn: sqlite3.Connection) -> list[str]:
    """Return all user table names (excluding sqlite internals)."""
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
    ).fetchall()
    return [r[0] for r in rows]


def export_table_as_dicts(
    conn: sqlite3.Connection,
    table_name: str,
    user_id: Optional[int] = None,
) -> list[dict]:
    """Return rows of a table as dicts, optionally filtered by user_id if column exists."""
    # Check if table has user_id column
    if user_id is not None and table_name != "schema_version":
        info = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
        cols = [c[1] for c in info]
        if "user_id" in cols:
            rows = conn.execute(f"SELECT * FROM {table_name} WHERE user_id = ?", (user_id,)).fetchall()
            return [dict(r) for r in rows]
        elif table_name == "user":
            rows = conn.execute("SELECT id, email, name, created_at FROM user WHERE id = ?", (user_id,)).fetchall()
            return [dict(r) for r in rows]

    rows = conn.execute(f"SELECT * FROM {table_name}").fetchall()
    return [dict(r) for r in rows]
