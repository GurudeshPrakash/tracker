"""Tests for lib/dates.py."""

from lib.dates import (
    today, add_days, week_start, week_end,
    date_range, weekday, days_between, last_day_of_month,
)


def test_today_format():
    """today() returns a valid YYYY-MM-DD string."""
    t = today()
    assert len(t) == 10
    assert t[4] == "-" and t[7] == "-"


def test_add_days():
    assert add_days("2025-01-01", 1) == "2025-01-02"
    assert add_days("2025-01-31", 1) == "2025-02-01"
    assert add_days("2025-03-01", -1) == "2025-02-28"


def test_add_days_zero():
    assert add_days("2025-06-15", 0) == "2025-06-15"


def test_week_start():
    # 2025-01-06 is a Monday
    assert week_start("2025-01-06") == "2025-01-06"
    # 2025-01-08 is Wednesday
    assert week_start("2025-01-08") == "2025-01-06"
    # 2025-01-12 is Sunday
    assert week_start("2025-01-12") == "2025-01-06"


def test_week_end():
    # 2025-01-06 is Monday -> Sunday is 2025-01-12
    assert week_end("2025-01-06") == "2025-01-12"
    assert week_end("2025-01-12") == "2025-01-12"


def test_date_range():
    result = date_range("2025-01-01", "2025-01-03")
    assert result == ["2025-01-01", "2025-01-02", "2025-01-03"]


def test_date_range_single_day():
    assert date_range("2025-06-15", "2025-06-15") == ["2025-06-15"]


def test_date_range_empty():
    assert date_range("2025-06-15", "2025-06-14") == []


def test_weekday():
    # 2025-01-06 is Monday = 0
    assert weekday("2025-01-06") == 0
    # 2025-01-12 is Sunday = 6
    assert weekday("2025-01-12") == 6


def test_days_between():
    assert days_between("2025-01-01", "2025-01-10") == 9
    assert days_between("2025-01-10", "2025-01-01") == -9


def test_last_day_of_month():
    assert last_day_of_month(2025, 2) == 28
    assert last_day_of_month(2024, 2) == 29  # leap year
    assert last_day_of_month(2025, 1) == 31
    assert last_day_of_month(2025, 4) == 30
