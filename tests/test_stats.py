"""Tests for stats service — spec Section 12 (Stats).

- Streak counts consecutive days; a gap resets it; today without update counts from yesterday.
- Empty database returns 0 / empty frames, never raises.
"""

import pandas as pd
from db import repository as repo
from services import stats


def test_streak_empty_db(db_conn):
    """Empty database returns streak of 0."""
    s = stats.update_streak("2025-01-10", db_conn)
    assert s == 0


def test_streak_consecutive_days(db_conn):
    """Streak counts consecutive days."""
    for date in ["2025-01-08", "2025-01-09", "2025-01-10"]:
        repo.upsert_daily_update(db_conn, date=date, planned_count=5, completed_count=3)

    s = stats.update_streak("2025-01-10", db_conn)
    assert s == 3


def test_streak_gap_resets(db_conn):
    """A gap in dates resets the streak."""
    repo.upsert_daily_update(db_conn, date="2025-01-07", planned_count=5, completed_count=3)
    # Gap on Jan 8
    repo.upsert_daily_update(db_conn, date="2025-01-09", planned_count=5, completed_count=3)
    repo.upsert_daily_update(db_conn, date="2025-01-10", planned_count=5, completed_count=3)

    s = stats.update_streak("2025-01-10", db_conn)
    assert s == 2  # Only Jan 9 and 10


def test_streak_today_without_update(db_conn):
    """If today has no update, count from yesterday."""
    repo.upsert_daily_update(db_conn, date="2025-01-08", planned_count=5, completed_count=3)
    repo.upsert_daily_update(db_conn, date="2025-01-09", planned_count=5, completed_count=3)
    # No update for Jan 10

    s = stats.update_streak("2025-01-10", db_conn)
    assert s == 2  # Jan 8 and 9


def test_completion_rate_empty(db_conn):
    """Empty database returns empty DataFrame."""
    df = stats.completion_rate_series("2025-01-01", "2025-01-10", db_conn)
    assert isinstance(df, pd.DataFrame)
    assert df.empty


def test_completion_rate_with_data(db_conn):
    """Completion rate uses daily_update snapshot counts."""
    repo.upsert_daily_update(db_conn, date="2025-01-10", planned_count=10, completed_count=7)
    df = stats.completion_rate_series("2025-01-10", "2025-01-10", db_conn)
    assert len(df) == 1
    assert df.iloc[0]["rate"] == 70.0


def test_study_minutes_by_skill_empty(db_conn):
    """Empty database returns empty DataFrame."""
    df = stats.study_minutes_by_skill("2025-01-01", "2025-01-10", db_conn)
    assert df.empty


def test_average_rating_empty(db_conn):
    """Empty database returns None."""
    r = stats.average_rating("2025-01-01", "2025-01-10", db_conn)
    assert r is None


def test_week_summary_empty(db_conn):
    """Week summary on empty DB returns zeros, never raises."""
    summary = stats.week_summary("2025-01-06", db_conn)
    assert summary["tasks_completed"] == 0
    assert summary["completion_rate"] == 0
    assert summary["study_hours"] == 0.0
