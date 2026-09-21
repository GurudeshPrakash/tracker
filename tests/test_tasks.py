"""Tests for task service — spec Section 12 (Tasks).

- Fourth top-3 task on one date raises ValueError.
- Completing sets completed_at and completed_date; un-completing clears them.
- Parent with open subtasks cannot be completed.
"""

import pytest
from db import repository as repo
from services import tasks as task_svc


def test_create_task(db_conn):
    """Create a basic task."""
    tid = task_svc.create_task(db_conn, title="Test task", planned_date="2025-01-10")
    task = repo.get_task(db_conn, tid)
    assert task is not None
    assert task.title == "Test task"
    assert task.status == "todo"
    assert task.planned_date == "2025-01-10"


def test_complete_sets_timestamps(db_conn):
    """Completing a task sets completed_at and completed_date."""
    tid = task_svc.create_task(db_conn, title="Complete me", planned_date="2025-01-10")
    task = task_svc.complete(tid, db_conn, today_date="2025-01-10")
    assert task.status == "done"
    assert task.completed_at is not None
    assert task.completed_date == "2025-01-10"


def test_uncomplete_clears_timestamps(db_conn):
    """Un-completing clears completed_at and completed_date."""
    tid = task_svc.create_task(db_conn, title="Toggle", planned_date="2025-01-10")
    task_svc.complete(tid, db_conn, today_date="2025-01-10")
    task = task_svc.uncomplete(tid, db_conn)
    assert task.status == "todo"
    assert task.completed_at is None
    assert task.completed_date is None


def test_top3_limit_of_3(db_conn):
    """Fourth top-3 task on one date raises ValueError."""
    date = "2025-01-10"
    ids = []
    for i in range(3):
        tid = task_svc.create_task(db_conn, title=f"Task {i}", planned_date=date)
        task_svc.set_top3(tid, True, db_conn)
        ids.append(tid)

    # Fourth should fail
    tid4 = task_svc.create_task(db_conn, title="Task 4", planned_date=date)
    with pytest.raises(ValueError, match="Only 3 priorities per day"):
        task_svc.set_top3(tid4, True, db_conn)


def test_top3_toggle_same_task(db_conn):
    """Toggling top-3 off and on for same task should work."""
    date = "2025-01-10"
    for i in range(3):
        tid = task_svc.create_task(db_conn, title=f"Task {i}", planned_date=date)
        task_svc.set_top3(tid, True, db_conn)

    # Toggle one off
    task_svc.set_top3(tid, False, db_conn)

    # Now add another
    tid_new = task_svc.create_task(db_conn, title="New", planned_date=date)
    task_svc.set_top3(tid_new, True, db_conn)  # Should work — only 3 active


def test_parent_cannot_complete_with_open_subtasks(db_conn):
    """Parent with open subtasks cannot be completed."""
    parent_id = task_svc.create_task(db_conn, title="Parent", planned_date="2025-01-10")
    sub_id = task_svc.create_task(
        db_conn, title="Subtask", planned_date="2025-01-10", parent_task_id=parent_id
    )

    with pytest.raises(ValueError, match="subtask"):
        task_svc.complete(parent_id, db_conn, today_date="2025-01-10")

    # Complete subtask first, then parent
    task_svc.complete(sub_id, db_conn, today_date="2025-01-10")
    task = task_svc.complete(parent_id, db_conn, today_date="2025-01-10")
    assert task.status == "done"


def test_drop_and_restore(db_conn):
    """Dropping and restoring a task."""
    tid = task_svc.create_task(db_conn, title="Dropme", planned_date="2025-01-10")
    task_svc.drop(tid, db_conn)
    task = repo.get_task(db_conn, tid)
    assert task.status == "dropped"

    task_svc.restore(tid, db_conn)
    task = repo.get_task(db_conn, tid)
    assert task.status == "todo"


def test_default_priority_and_category(db_conn):
    """Default priority is medium and category is work."""
    tid = task_svc.create_task(db_conn, title="Defaults", planned_date="2025-01-10")
    task = repo.get_task(db_conn, tid)
    assert task.priority == "medium"
    assert task.category == "work"
