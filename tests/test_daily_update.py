"""Tests for daily update service — spec Section 12 (Daily update).

- close_day stores correct planned_count and completed_count.
- Unchecked open tasks become dropped; checked ones move to next day.
- Editing a closed day does not trigger a second rollover.
- Prefill includes completed task titles and session minutes.
"""

from db import repository as repo
from db.models import DailyUpdateForm
from services import tasks as task_svc
from services import daily_update as du_svc
from services import learning as learn_svc


def test_close_day_snapshot_counts(db_conn):
    """close_day stores correct planned_count and completed_count."""
    # Create 3 tasks, complete 2
    t1 = task_svc.create_task(db_conn, title="Task 1", planned_date="2025-01-10")
    t2 = task_svc.create_task(db_conn, title="Task 2", planned_date="2025-01-10")
    t3 = task_svc.create_task(db_conn, title="Task 3", planned_date="2025-01-10")
    task_svc.complete(t1, db_conn, today_date="2025-01-10")
    task_svc.complete(t2, db_conn, today_date="2025-01-10")

    form = DailyUpdateForm(completed_summary="Did stuff", day_rating=4)
    update = du_svc.close_day("2025-01-10", form, carry_task_ids=[t3], conn=db_conn)

    assert update.planned_count == 3  # 2 done + 1 todo
    assert update.completed_count == 2


def test_unchecked_tasks_dropped(db_conn):
    """Tasks not in carry_task_ids become dropped."""
    t1 = task_svc.create_task(db_conn, title="Keep", planned_date="2025-01-10")
    t2 = task_svc.create_task(db_conn, title="Drop", planned_date="2025-01-10")

    form = DailyUpdateForm()
    du_svc.close_day("2025-01-10", form, carry_task_ids=[t1], conn=db_conn)

    task1 = repo.get_task(db_conn, t1)
    task2 = repo.get_task(db_conn, t2)

    # t1 was carried (rolled over to tomorrow)
    assert task1.planned_date == "2025-01-11"
    assert task1.status == "todo"

    # t2 was dropped
    assert task2.status == "dropped"


def test_carried_tasks_move_to_next_day(db_conn):
    """Checked tasks roll over to the next day."""
    t1 = task_svc.create_task(db_conn, title="Carry me", planned_date="2025-01-10")

    form = DailyUpdateForm()
    du_svc.close_day("2025-01-10", form, carry_task_ids=[t1], conn=db_conn)

    task = repo.get_task(db_conn, t1)
    assert task.planned_date == "2025-01-11"
    assert task.rollover_count == 1


def test_edit_closed_day_no_second_rollover(db_conn):
    """Editing a closed day does not trigger a second rollover."""
    t1 = task_svc.create_task(db_conn, title="Carry", planned_date="2025-01-10")

    form = DailyUpdateForm(completed_summary="First close")
    du_svc.close_day("2025-01-10", form, carry_task_ids=[t1], conn=db_conn)

    task = repo.get_task(db_conn, t1)
    assert task.rollover_count == 1

    # Re-opening and saving text edits should use upsert without rollover
    update = repo.get_daily_update(db_conn, "2025-01-10")
    assert update is not None
    repo.upsert_daily_update(
        db_conn, date="2025-01-10",
        planned_count=update.planned_count,
        completed_count=update.completed_count,
        completed_summary="Updated text",
    )

    # Task should still have rollover_count == 1
    task = repo.get_task(db_conn, t1)
    assert task.rollover_count == 1


def test_prefill_includes_completed_titles(db_conn):
    """Prefill has completed task titles."""
    t1 = task_svc.create_task(db_conn, title="Done Task A", planned_date="2025-01-10")
    task_svc.complete(t1, db_conn, today_date="2025-01-10")

    prefill = du_svc.build_prefill("2025-01-10", db_conn)
    assert len(prefill["completed_tasks"]) == 1
    assert prefill["completed_tasks"][0].title == "Done Task A"


def test_prefill_includes_session_minutes(db_conn):
    """Prefill has study minutes from sessions."""
    # Create a learning item and session
    item_id = repo.create_learning_item(db_conn, skill="SQL", resource="Tutorial")
    repo.create_learning_session(
        db_conn, learning_item_id=item_id, session_date="2025-01-10",
        duration_min=45, takeaway="Learned joins"
    )

    prefill = du_svc.build_prefill("2025-01-10", db_conn)
    assert prefill["study_minutes"] == 45
    assert "Learned joins" in prefill["session_takeaways"]
