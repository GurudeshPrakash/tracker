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


def build_prefill(date: str, conn: sqlite3.Connection) -> dict:
    """Build pre-fill data for the daily update form.

    Returns:
        completed_tasks: list[Task] — tasks completed on this date
        open_tasks: list[Task] — todo tasks planned for this date
        study_minutes: int — sum of session durations on this date
        session_takeaways: list[str] — takeaways logged on this date
        existing: DailyUpdate | None — existing update if day was already closed
    """
    completed_tasks = repo.get_done_tasks_for_date(conn, date)
    open_tasks = repo.get_todo_tasks_for_date(conn, date)
    study_minutes = repo.study_minutes_for_date(conn, date)
    session_takeaways = repo.takeaways_for_date(conn, date)
    existing = repo.get_daily_update(conn, date)

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
) -> DailyUpdate:
    """Close the day in a single transaction.

    Steps (Section 7.4):
    1. planned_count = tasks that were planned for date (todo + done with completed_date == date)
    2. completed_count = tasks with completed_date == date
    3. Upsert daily_update for date (form values + snapshot counts)
    4. For open tasks NOT in carry_task_ids: set status='dropped'
    5. rollover(date, next_day) for the carried tasks

    Returns the saved DailyUpdate.
    """
    # Start transaction
    open_tasks = repo.get_todo_tasks_for_date(conn, date)
    planned_count = repo.count_planned_for_date(conn, date)
    completed_count = repo.count_completed_for_date(conn, date)

    # Upsert daily update
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
    )

    # Drop tasks not being carried
    carry_set = set(carry_task_ids)
    for task in open_tasks:
        if task.id not in carry_set:
            repo.drop_task(conn, task.id)

    # Rollover the carried tasks
    next_day = add_days(date, 1)
    rollover(date, next_day, conn)

    return repo.get_daily_update(conn, date)
