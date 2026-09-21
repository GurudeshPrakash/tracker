"""Tests for rollover service — spec Section 12 (Rollover).

- Moves todo tasks with planned_date <= from_date, increments rollover_count.
- Leaves done, dropped and backlog (NULL date) tasks untouched.
- Running twice moves nothing the second time, no double-increment.
- Close day then startup rollover yields rollover_count == 1, not 2.
- Missed day (no close) then startup rollover moves tasks to today with count +1.
- is_top3 is preserved.
"""

from db import repository as repo
from services import tasks as task_svc
from services.rollover import rollover


def test_basic_rollover(db_conn):
    """Moves todo tasks and increments rollover_count."""
    tid = task_svc.create_task(db_conn, title="Roll me", planned_date="2025-01-10")
    moved = rollover("2025-01-10", "2025-01-11", db_conn)
    assert moved == 1

    task = repo.get_task(db_conn, tid)
    assert task.planned_date == "2025-01-11"
    assert task.rollover_count == 1


def test_leaves_done_untouched(db_conn):
    """Done tasks are not moved."""
    tid = task_svc.create_task(db_conn, title="Done task", planned_date="2025-01-10")
    task_svc.complete(tid, db_conn, today_date="2025-01-10")

    moved = rollover("2025-01-10", "2025-01-11", db_conn)
    assert moved == 0

    task = repo.get_task(db_conn, tid)
    assert task.status == "done"


def test_leaves_dropped_untouched(db_conn):
    """Dropped tasks are not moved."""
    tid = task_svc.create_task(db_conn, title="Dropped", planned_date="2025-01-10")
    task_svc.drop(tid, db_conn)

    moved = rollover("2025-01-10", "2025-01-11", db_conn)
    assert moved == 0


def test_leaves_backlog_untouched(db_conn):
    """Backlog (NULL planned_date) tasks are not moved."""
    tid = task_svc.create_task(db_conn, title="Backlog", planned_date=None)

    moved = rollover("2025-01-10", "2025-01-11", db_conn)
    assert moved == 0

    task = repo.get_task(db_conn, tid)
    assert task.planned_date is None


def test_idempotent_rollover(db_conn):
    """Running rollover twice moves nothing the second time."""
    tid = task_svc.create_task(db_conn, title="Once", planned_date="2025-01-10")

    first = rollover("2025-01-10", "2025-01-11", db_conn)
    assert first == 1

    second = rollover("2025-01-10", "2025-01-11", db_conn)
    assert second == 0

    task = repo.get_task(db_conn, tid)
    assert task.rollover_count == 1  # Not 2


def test_close_day_then_startup_rollover_count_1(db_conn):
    """Close day (evening rollover to tomorrow) then startup rollover
    yields rollover_count == 1, not 2."""
    tid = task_svc.create_task(db_conn, title="Carry", planned_date="2025-01-10")

    # Evening: close day moves to Jan 11
    rollover("2025-01-10", "2025-01-11", db_conn)

    # Next morning startup: rollover(yesterday=Jan 10, today=Jan 11)
    # Should find nothing because task is already at Jan 11
    moved = rollover("2025-01-10", "2025-01-11", db_conn)
    assert moved == 0

    task = repo.get_task(db_conn, tid)
    assert task.rollover_count == 1


def test_missed_day_startup_rollover(db_conn):
    """Skip closing a day; next day startup moves tasks to today."""
    tid = task_svc.create_task(db_conn, title="Missed", planned_date="2025-01-10")

    # No close on Jan 10. On Jan 11 morning, startup runs rollover(Jan 10, Jan 11)
    moved = rollover("2025-01-10", "2025-01-11", db_conn)
    assert moved == 1

    task = repo.get_task(db_conn, tid)
    assert task.planned_date == "2025-01-11"
    assert task.rollover_count == 1


def test_top3_preserved(db_conn):
    """is_top3 flag is preserved after rollover."""
    tid = task_svc.create_task(db_conn, title="Priority", planned_date="2025-01-10")
    task_svc.set_top3(tid, True, db_conn)

    rollover("2025-01-10", "2025-01-11", db_conn)

    task = repo.get_task(db_conn, tid)
    assert task.is_top3 == 1
    assert task.planned_date == "2025-01-11"
