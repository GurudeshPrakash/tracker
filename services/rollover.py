"""Rollover service — carry unfinished tasks forward.

Must be idempotent: after a rollover, no todo task has planned_date <= from_date,
so a second run finds nothing to move.
"""

from __future__ import annotations

import sqlite3

from db import repository as repo


def rollover(from_date: str, to_date: str, conn: sqlite3.Connection) -> int:
    """Move every todo task with planned_date <= from_date to to_date.

    Increments rollover_count by 1. Returns number of tasks moved.
    Does not touch tasks with planned_date IS NULL (backlog), done, or dropped.

    This is idempotent: after a rollover, no todo task has
    planned_date <= from_date, so calling again moves nothing.
    """
    return repo.rollover_tasks(conn, from_date, to_date)
