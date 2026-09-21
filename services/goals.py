"""Goals service — progress calculation and status.

Rules from spec Section 7.6.
"""

from __future__ import annotations

import sqlite3

from db import repository as repo
from db.models import Goal
from lib.dates import week_start, week_end, weekday, days_between


def goal_progress(goal_id: int, today: str, conn: sqlite3.Connection) -> dict:
    """Calculate goal progress and status.

    Returns:
        done_hours: float — all-time hours from linked learning items' sessions
        week_hours: float — hours this Mon-Sun week
        target_hours: float
        percent: float — total_hours: done/target; weekly_hours: week/target
        expected_percent: float | None — for total_hours goals only
        status: 'on_track' | 'behind' | 'ahead' | 'complete'
    """
    goal = repo.get_goal(conn, goal_id)
    if goal is None:
        return {
            "done_hours": 0.0, "week_hours": 0.0, "target_hours": 0.0,
            "percent": 0.0, "expected_percent": None, "status": "on_track",
        }

    # All-time minutes
    total_min = repo.total_study_minutes_for_goal(conn, goal_id)
    done_hours = total_min / 60.0

    # This week's minutes
    ws = week_start(today)
    we = week_end(today)
    week_min = repo.study_minutes_for_goal(conn, goal_id, ws, we)
    week_hours = week_min / 60.0

    target_hours = goal.target_hours

    if goal.target_type == "weekly_hours":
        percent = (week_hours / target_hours * 100) if target_hours > 0 else 0
        expected_percent = None

        # Behind rule: on day k (Mon=1..Sun=7), behind if week_hours < target * (k-1) / 7
        day_k = weekday(today) + 1  # weekday() returns 0=Mon, so +1 gives 1=Mon..7=Sun
        threshold = target_hours * (day_k - 1) / 7

        if week_hours >= target_hours:
            status = "complete"
        elif week_hours < threshold:
            status = "behind"
        else:
            status = "on_track"

    else:  # total_hours
        percent = (done_hours / target_hours * 100) if target_hours > 0 else 0

        if goal.target_date:
            total_days = max(1, days_between(goal.start_date, goal.target_date))
            elapsed_days = max(0, days_between(goal.start_date, today))
            expected_percent = min(100, max(0, elapsed_days / total_days * 100))
        else:
            expected_percent = None

        if percent >= 100:
            status = "complete"
        elif expected_percent is not None:
            if percent < expected_percent - 10:
                status = "behind"
            elif percent > expected_percent + 10:
                status = "ahead"
            else:
                status = "on_track"
        else:
            status = "on_track"

    return {
        "done_hours": done_hours,
        "week_hours": week_hours,
        "target_hours": target_hours,
        "percent": percent,
        "expected_percent": expected_percent,
        "status": status,
    }
