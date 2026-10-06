"""Daily update service — build prefill and close-day logic.

close_day runs in a single transaction as specified in Section 7.4.
"""

from __future__ import annotations

import sqlite3
from typing import Optional

from db import repository as repo
from db.models import Task, DailyUpdate, DailyUpdateForm
from lib.dates import add_days
from services.rollover import rollover


def build_prefill(date: str, conn: sqlite3.Connection, user_id: Optional[int] = None) -> dict:
    """Build pre-fill data for the daily update form."""
    completed_tasks = repo.get_done_tasks_for_date(conn, date, user_id=user_id)
    open_tasks = repo.get_todo_tasks_for_date(conn, date, user_id=user_id)
    study_minutes = repo.study_minutes_for_date(conn, date, user_id=user_id)
    session_takeaways = repo.takeaways_for_date(conn, date, user_id=user_id)
    existing = repo.get_daily_update(conn, date, user_id=user_id)

    return {
        "completed_tasks": completed_tasks,
        "open_tasks": open_tasks,
        "study_minutes": study_minutes,
        "session_takeaways": session_takeaways,
        "existing": existing,
    }


def close_day(
    date: str,
    form: DailyUpdateForm,
    carry_task_ids: list[int],
    conn: sqlite3.Connection,
    user_id: Optional[int] = None,
) -> DailyUpdate:
    """Close the day in a single transaction."""
    existing = repo.get_daily_update(conn, date, user_id=user_id)
    if existing:
        # Reflection edits after close-out must not drop or rollover again.
        repo.upsert_daily_update(
            conn,
            date=date,
            planned_count=existing.planned_count,
            completed_count=existing.completed_count,
            completed_summary=form.completed_summary,
            learned_today=form.learned_today,
            study_minutes=form.study_minutes,
            day_rating=form.day_rating,
            blockers=form.blockers,
            tomorrow_focus=form.tomorrow_focus,
            user_id=user_id,
        )
        return repo.get_daily_update(conn, date, user_id=user_id)

    open_tasks = repo.get_todo_tasks_for_date(conn, date, user_id=user_id)
    planned_count = repo.count_planned_for_date(conn, date, user_id=user_id)
    completed_count = repo.count_completed_for_date(conn, date, user_id=user_id)

    repo.upsert_daily_update(
        conn,
        date=date,
        planned_count=planned_count,
        completed_count=completed_count,
        completed_summary=form.completed_summary,
        learned_today=form.learned_today,
        study_minutes=form.study_minutes,
        day_rating=form.day_rating,
        blockers=form.blockers,
        tomorrow_focus=form.tomorrow_focus,
        user_id=user_id,
    )

    carry_set = set(carry_task_ids)
    for task in open_tasks:
        if task.id not in carry_set:
            repo.drop_task(conn, task.id, user_id=user_id)

    next_day = add_days(date, 1)
    rollover(date, next_day, conn, user_id=user_id)

    return repo.get_daily_update(conn, date, user_id=user_id)
