"""Date utility functions.

All dates are local ISO strings (YYYY-MM-DD).
Tests can override today() by monkeypatching this module.
"""

from __future__ import annotations

import datetime


def today() -> str:
    """Return today's local date as 'YYYY-MM-DD'."""
    return datetime.date.today().isoformat()


def add_days(iso: str, n: int) -> str:
    """Add n days to an ISO date string."""
    d = datetime.date.fromisoformat(iso)
    return (d + datetime.timedelta(days=n)).isoformat()


def week_start(iso: str) -> str:
    """Return the Monday of the week containing the given date."""
    d = datetime.date.fromisoformat(iso)
    monday = d - datetime.timedelta(days=d.weekday())
    return monday.isoformat()


def week_end(iso: str) -> str:
    """Return the Sunday of the week containing the given date."""
    d = datetime.date.fromisoformat(iso)
    sunday = d + datetime.timedelta(days=6 - d.weekday())
    return sunday.isoformat()


def date_range(start: str, end: str) -> list[str]:
    """Return a list of ISO date strings from start to end, inclusive."""
    s = datetime.date.fromisoformat(start)
    e = datetime.date.fromisoformat(end)
    result = []
    current = s
    while current <= e:
        result.append(current.isoformat())
        current += datetime.timedelta(days=1)
    return result


def weekday(iso: str) -> int:
    """Return the weekday of an ISO date. 0 = Monday, 6 = Sunday."""
    return datetime.date.fromisoformat(iso).weekday()


def days_between(start: str, end: str) -> int:
    """Return the number of days between two dates (end - start)."""
    s = datetime.date.fromisoformat(start)
    e = datetime.date.fromisoformat(end)
    return (e - s).days


def last_day_of_month(year: int, month: int) -> int:
    """Return the last day of a given month."""
    import calendar
    return calendar.monthrange(year, month)[1]
