"""Learning service — sessions, totals, takeaways.

This module never imports Streamlit.
"""

from __future__ import annotations

import sqlite3
from typing import Optional

from db import repository as repo
from lib.dates import today, week_start, week_end


def log_session(
    item_id: int,
    session_date: str,
    duration_min: int,
    takeaway: str,
    confidence: int | None = None,
    task_id: int | None = None,
    conn: sqlite3.Connection = None,
) -> int:
    """Log a study session.

    Args:
        item_id: The learning item studied.
        session_date: Date of the session (YYYY-MM-DD).
        duration_min: Duration in minutes (must be > 0).
        takeaway: What was learned (required, must be non-empty).
        confidence: Self-assessed confidence 1-5 (optional).
        task_id: Optional linked completed task.
        conn: Database connection.

    Returns:
        The new session id.

    Raises:
        ValueError: If takeaway is empty or duration_min <= 0.
    """
    takeaway_stripped = takeaway.strip()
    if not takeaway_stripped:
        raise ValueError("Takeaway is required and must be non-empty")
    if duration_min <= 0:
        raise ValueError("Duration must be greater than 0")

    session_id = repo.create_learning_session(
        conn,
        learning_item_id=item_id,
        session_date=session_date,
        duration_min=duration_min,
        takeaway=takeaway_stripped,
        confidence=confidence,
        task_id=task_id,
    )

    # If linked to a task, set its actual_min if empty
    if task_id:
        task = repo.get_task(conn, task_id)
        if task and task.actual_min is None:
            repo.update_task(conn, task_id, actual_min=duration_min)

    return session_id


def totals_by_skill(start: str, end: str, conn: sqlite3.Connection) -> list[dict]:
    """Return skill totals for a date range.

    Returns list of dicts with keys: skill, minutes, sessions, avg_confidence.
    """
    rows = conn.execute(
        """SELECT li.skill,
                  SUM(ls.duration_min) as minutes,
                  COUNT(*) as sessions,
                  AVG(ls.confidence) as avg_confidence
           FROM learning_session ls
           JOIN learning_item li ON ls.learning_item_id = li.id
           WHERE ls.session_date BETWEEN ? AND ?
           GROUP BY li.skill
           ORDER BY minutes DESC""",
        (start, end),
    ).fetchall()
    return [dict(r) for r in rows]


def minutes_for_goal(goal_id: int, start: str, end: str, conn: sqlite3.Connection) -> int:
    """Return total study minutes for sessions linked to a goal in a date range."""
    return repo.study_minutes_for_goal(conn, goal_id, start, end)


def recent_takeaways(limit: int = 20, conn: sqlite3.Connection = None) -> list[dict]:
    """Return recent takeaways with skill and resource info."""
    rows = conn.execute(
        """SELECT ls.takeaway, ls.session_date, ls.duration_min, ls.confidence,
                  li.skill, li.resource
           FROM learning_session ls
           JOIN learning_item li ON ls.learning_item_id = li.id
           ORDER BY ls.session_date DESC, ls.created_at DESC
           LIMIT ?""",
        (limit,),
    ).fetchall()
    return [dict(r) for r in rows]
