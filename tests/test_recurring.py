"""Tests for recurring tasks service — spec Section 12 (Recurring).

- Weekdays rule skips Saturday and Sunday.
- Calling generate twice creates one task (idempotent).
- Monthly rule on day 31 falls back to last day in shorter months.
"""

from db import repository as repo
from services import recurring as rec_svc


def _create_recurring(db_conn, rule="daily", weekday=None, day_of_month=None, start="2025-01-01"):
    """Helper to create a recurring task."""
    return repo.create_recurring_task(
        db_conn, title="Recurring Task", rule=rule,
        start_date=start, weekday=weekday, day_of_month=day_of_month,
    )


def test_daily_generates_every_day(db_conn):
    """Daily rule generates a task every day."""
    rec_id = _create_recurring(db_conn, rule="daily")

    count = rec_svc.generate_for_date("2025-01-10", db_conn)
    assert count == 1

    tasks = repo.get_todo_tasks_for_date(db_conn, "2025-01-10")
    assert len(tasks) == 1
    assert tasks[0].recurring_id == rec_id


def test_weekdays_skip_saturday(db_conn):
    """Weekdays rule skips Saturday (2025-01-11 is Saturday)."""
    _create_recurring(db_conn, rule="weekdays")

    # Friday
    count_fri = rec_svc.generate_for_date("2025-01-10", db_conn)
    assert count_fri == 1

    # Saturday
    count_sat = rec_svc.generate_for_date("2025-01-11", db_conn)
    assert count_sat == 0


def test_weekdays_skip_sunday(db_conn):
    """Weekdays rule skips Sunday (2025-01-12 is Sunday)."""
    _create_recurring(db_conn, rule="weekdays")

    count = rec_svc.generate_for_date("2025-01-12", db_conn)
    assert count == 0


def test_weekly_correct_day(db_conn):
    """Weekly rule only generates on the specified weekday."""
    # weekday=2 = Wednesday. 2025-01-08 is Wednesday.
    _create_recurring(db_conn, rule="weekly", weekday=2)

    # Wednesday
    count_wed = rec_svc.generate_for_date("2025-01-08", db_conn)
    assert count_wed == 1

    # Thursday
    count_thu = rec_svc.generate_for_date("2025-01-09", db_conn)
    assert count_thu == 0


def test_idempotent_generation(db_conn):
    """Calling generate twice creates one task only."""
    _create_recurring(db_conn, rule="daily")

    count1 = rec_svc.generate_for_date("2025-01-10", db_conn)
    count2 = rec_svc.generate_for_date("2025-01-10", db_conn)

    assert count1 == 1
    assert count2 == 0

    tasks = repo.get_todo_tasks_for_date(db_conn, "2025-01-10")
    assert len(tasks) == 1


def test_monthly_day_31_fallback(db_conn):
    """Monthly rule on day 31 falls back to last day in shorter months."""
    _create_recurring(db_conn, rule="monthly", day_of_month=31)

    # February 2025 has 28 days
    count = rec_svc.generate_for_date("2025-02-28", db_conn)
    assert count == 1

    # Feb 27 should not generate
    count_27 = rec_svc.generate_for_date("2025-02-27", db_conn)
    assert count_27 == 0


def test_before_start_date_no_generate(db_conn):
    """Tasks before start_date are not generated."""
    _create_recurring(db_conn, rule="daily", start="2025-02-01")

    count = rec_svc.generate_for_date("2025-01-31", db_conn)
    assert count == 0


def test_after_end_date_no_generate(db_conn):
    """Tasks after end_date are not generated."""
    rec_id = repo.create_recurring_task(
        db_conn, title="Ending", rule="daily",
        start_date="2025-01-01", end_date="2025-01-10",
    )

    count = rec_svc.generate_for_date("2025-01-11", db_conn)
    assert count == 0
