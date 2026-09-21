"""Recurring tasks service — generate task instances from recurring templates.

Rules from spec Section 7.8. Generation is idempotent via the unique index
on task(recurring_id, planned_date) and INSERT OR IGNORE.
"""

from __future__ import annotations

import sqlite3
import datetime

from db import repository as repo
from lib.dates import weekday, last_day_of_month


def generate_for_date(date: str, conn: sqlite3.Connection) -> int:
    """Generate recurring task instances for a given date.

    For each active recurring_task where start_date <= date and
    (end_date is null or >= date):
    - daily: always
    - weekdays: Mon-Fri only
    - weekly: only if weekday(date) == the template's weekday field
    - monthly: only if date.day == day_of_month (or last day of month if shorter)

    Uses INSERT OR IGNORE for idempotency. Does not backfill missed days.

    Args:
        date: The date to generate for (YYYY-MM-DD).
        conn: Database connection.

    Returns:
        Number of tasks created.
    """
    recurring_tasks = repo.get_active_recurring_tasks(conn)
    count = 0

    d = datetime.date.fromisoformat(date)
    wd = weekday(date)  # 0 = Monday

    for rt in recurring_tasks:
        # Check date bounds
        if rt.start_date > date:
            continue
        if rt.end_date and rt.end_date < date:
            continue

        # Check rule
        should_generate = False

        if rt.rule == "daily":
            should_generate = True
        elif rt.rule == "weekdays":
            should_generate = wd <= 4  # Mon-Fri
        elif rt.rule == "weekly":
            should_generate = wd == rt.weekday
        elif rt.rule == "monthly":
            target_day = rt.day_of_month
            last_day = last_day_of_month(d.year, d.month)
            # If month is shorter, use last day
            effective_day = min(target_day, last_day)
            should_generate = d.day == effective_day

        if should_generate:
            inserted = repo.insert_recurring_task_instance(conn, rt, date)
            if inserted:
                count += 1

    return count
