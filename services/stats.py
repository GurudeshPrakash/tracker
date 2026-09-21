"""Stats service — streaks, completion rates, weekly totals.

Rules from spec Section 7.9.
"""

from __future__ import annotations

import sqlite3

import pandas as pd

from db import repository as repo
from lib.dates import today, add_days, week_start, week_end, date_range, days_between


def update_streak(today_date: str, conn: sqlite3.Connection) -> int:
    """Count consecutive calendar days ending today (or yesterday if today
    has no update yet) that each have a daily_update row.

    Returns the streak length (0 if no updates at all).
    """
    all_dates = repo.get_all_update_dates(conn)
    if not all_dates:
        return 0

    # Start from today or yesterday
    check_date = today_date
    if check_date not in all_dates:
        check_date = add_days(today_date, -1)
        if check_date not in all_dates:
            return 0

    # Count backwards
    date_set = set(all_dates)
    streak = 0
    current = check_date
    while current in date_set:
        streak += 1
        current = add_days(current, -1)

    return streak


def completion_rate_series(start: str, end: str, conn: sqlite3.Connection) -> pd.DataFrame:
    """Return a DataFrame with columns: date, planned, completed, rate.

    Uses daily_update snapshot counts for accuracy.
    """
    updates = repo.get_daily_updates_in_range(conn, start, end)
    if not updates:
        return pd.DataFrame(columns=["date", "planned", "completed", "rate"])

    data = []
    for u in updates:
        rate = (u.completed_count / u.planned_count * 100) if u.planned_count > 0 else 0
        data.append({
            "date": u.date,
            "planned": u.planned_count,
            "completed": u.completed_count,
            "rate": round(rate, 1),
        })
    return pd.DataFrame(data)


def minutes_by_category(start: str, end: str, conn: sqlite3.Connection) -> pd.DataFrame:
    """Return DataFrame with columns: category, minutes (sum of actual_min of done tasks)."""
    tasks = repo.get_done_tasks_in_range(conn, start, end)
    if not tasks:
        return pd.DataFrame(columns=["category", "minutes"])

    data = {}
    for t in tasks:
        mins = t.actual_min or 0
        data[t.category] = data.get(t.category, 0) + mins

    return pd.DataFrame([
        {"category": cat, "minutes": mins}
        for cat, mins in sorted(data.items())
    ])


def study_minutes_by_skill(start: str, end: str, conn: sqlite3.Connection) -> pd.DataFrame:
    """Return DataFrame with columns: skill, minutes."""
    rows = conn.execute(
        """SELECT li.skill, COALESCE(SUM(ls.duration_min), 0) as minutes
           FROM learning_session ls
           JOIN learning_item li ON ls.learning_item_id = li.id
           WHERE ls.session_date BETWEEN ? AND ?
           GROUP BY li.skill
           ORDER BY minutes DESC""",
        (start, end),
    ).fetchall()
    if not rows:
        return pd.DataFrame(columns=["skill", "minutes"])
    return pd.DataFrame([dict(r) for r in rows])


def study_minutes_per_week(weeks: int, today_date: str, conn: sqlite3.Connection) -> pd.DataFrame:
    """Return DataFrame with columns: week_start, minutes for the last N weeks."""
    data = []
    ws = week_start(today_date)
    for i in range(weeks):
        current_ws = add_days(ws, -7 * i)
        current_we = week_end(current_ws)
        rows = conn.execute(
            "SELECT COALESCE(SUM(duration_min), 0) FROM learning_session WHERE session_date BETWEEN ? AND ?",
            (current_ws, current_we),
        ).fetchone()
        data.append({"week_start": current_ws, "minutes": rows[0]})

    data.reverse()
    return pd.DataFrame(data)


def average_rating(start: str, end: str, conn: sqlite3.Connection) -> float | None:
    """Return average day_rating from daily_updates in range, or None."""
    row = conn.execute(
        "SELECT AVG(day_rating) FROM daily_update WHERE date BETWEEN ? AND ? AND day_rating IS NOT NULL",
        (start, end),
    ).fetchone()
    val = row[0]
    return round(val, 1) if val is not None else None


def week_summary(week_start_date: str, conn: sqlite3.Connection) -> dict:
    """Return a summary dict for a given week.

    Returns: tasks_completed, completion_rate, study_hours, avg_rating,
    best_day, top_skill, blockers, takeaways.
    """
    we = week_end(week_start_date)

    # Tasks completed
    tasks_completed = repo.count_done_tasks_in_range(conn, week_start_date, we)

    # Completion rate from daily updates
    updates = repo.get_daily_updates_in_range(conn, week_start_date, we)
    total_planned = sum(u.planned_count for u in updates)
    total_completed = sum(u.completed_count for u in updates)
    completion_rate = (total_completed / total_planned * 100) if total_planned > 0 else 0

    # Study hours
    study_row = conn.execute(
        "SELECT COALESCE(SUM(duration_min), 0) FROM learning_session WHERE session_date BETWEEN ? AND ?",
        (week_start_date, we),
    ).fetchone()
    study_hours = round(study_row[0] / 60, 1)

    # Average rating
    avg_rat = average_rating(week_start_date, we, conn)

    # Best day (highest rating, ties broken by most tasks completed)
    best_day = None
    if updates:
        rated = [u for u in updates if u.day_rating is not None]
        if rated:
            best = max(rated, key=lambda u: (u.day_rating, u.completed_count))
            best_day = {"date": best.date, "rating": best.day_rating, "completed": best.completed_count}

    # Top skill by minutes
    skill_df = study_minutes_by_skill(week_start_date, we, conn)
    top_skill = skill_df.iloc[0]["skill"] if not skill_df.empty else None

    # Blockers from daily updates
    blockers = [u.blockers for u in updates if u.blockers]

    # Takeaways from sessions
    takeaway_rows = conn.execute(
        "SELECT takeaway FROM learning_session WHERE session_date BETWEEN ? AND ? ORDER BY session_date",
        (week_start_date, we),
    ).fetchall()
    takeaways = [r[0] for r in takeaway_rows]

    return {
        "tasks_completed": tasks_completed,
        "completion_rate": round(completion_rate, 1),
        "study_hours": study_hours,
        "avg_rating": avg_rat,
        "best_day": best_day,
        "top_skill": top_skill,
        "blockers": blockers,
        "takeaways": takeaways,
    }
