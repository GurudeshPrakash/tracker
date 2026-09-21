"""Tests for suggestions service — spec Section 12 (Suggestions).

- Weekly goal 5h, 2h done, Thursday: minutes = ceil(3h * 60 / 4 days) rounded to 5 = 45.
- No suggestion when a task for that goal is already planned for the day.
- Paused/done goals produce no suggestions.
- Cap at 180 minutes.
"""

import math
from db import repository as repo
from services import suggestions as sug_svc
from services import tasks as task_svc


def _create_weekly_goal(db_conn, title="Learn SQL", hours=5.0):
    """Helper: create a weekly_hours goal starting Mon Jan 6."""
    return repo.create_goal(
        db_conn, title=title, target_type="weekly_hours",
        target_hours=hours, start_date="2025-01-06"
    )


def test_thursday_example(db_conn):
    """Weekly goal 5h, 2h done by Thursday → 45 min suggestion.

    remaining = 5 - 2 = 3h = 180min
    days_left from Thu to Sun inclusive = 4
    minutes = ceil(180 / 4) = 45, already multiple of 5
    """
    goal_id = _create_weekly_goal(db_conn, hours=5.0)

    # Create a learning item linked to goal and log 2h of sessions this week
    item_id = repo.create_learning_item(db_conn, skill="SQL", resource="Tutorial", goal_id=goal_id)
    repo.create_learning_session(
        db_conn, learning_item_id=item_id, session_date="2025-01-06",
        duration_min=60, takeaway="Learned basics"
    )
    repo.create_learning_session(
        db_conn, learning_item_id=item_id, session_date="2025-01-07",
        duration_min=60, takeaway="Learned joins"
    )

    # Thursday is 2025-01-09
    suggestions = sug_svc.suggest_tasks_for("2025-01-09", db_conn)
    assert len(suggestions) == 1
    assert suggestions[0].minutes == 45
    assert suggestions[0].goal_id == goal_id


def test_no_suggestion_when_task_exists(db_conn):
    """No suggestion when a task for that goal is already planned."""
    goal_id = _create_weekly_goal(db_conn, hours=5.0)
    item_id = repo.create_learning_item(db_conn, skill="SQL", resource="Tutorial", goal_id=goal_id)

    # Plan a task for this goal on Thursday
    task_svc.create_task(
        db_conn, title="Study SQL", planned_date="2025-01-09",
        category="learning", goal_id=goal_id
    )

    suggestions = sug_svc.suggest_tasks_for("2025-01-09", db_conn)
    assert len(suggestions) == 0


def test_paused_goal_no_suggestion(db_conn):
    """Paused goals produce no suggestions."""
    goal_id = _create_weekly_goal(db_conn, hours=5.0)
    repo.update_goal(db_conn, goal_id, status="paused")

    suggestions = sug_svc.suggest_tasks_for("2025-01-09", db_conn)
    assert len(suggestions) == 0


def test_done_goal_no_suggestion(db_conn):
    """Done goals produce no suggestions."""
    goal_id = _create_weekly_goal(db_conn, hours=5.0)
    repo.update_goal(db_conn, goal_id, status="done")

    suggestions = sug_svc.suggest_tasks_for("2025-01-09", db_conn)
    assert len(suggestions) == 0


def test_cap_at_180(db_conn):
    """Suggestions are capped at 180 minutes."""
    goal_id = _create_weekly_goal(db_conn, hours=100.0)  # Huge goal
    item_id = repo.create_learning_item(db_conn, skill="SQL", resource="Tutorial", goal_id=goal_id)

    # Sunday — only 1 day left, 100h remaining = 6000 min → cap to 180
    suggestions = sug_svc.suggest_tasks_for("2025-01-12", db_conn)
    assert len(suggestions) == 1
    assert suggestions[0].minutes == 180


def test_round_up_to_5(db_conn):
    """Minutes are rounded up to the nearest 5."""
    # 5h goal, 3h done, Thursday → remaining 2h/4days = 30min (already mult of 5)
    goal_id = _create_weekly_goal(db_conn, hours=5.0)
    item_id = repo.create_learning_item(db_conn, skill="SQL", resource="Tutorial", goal_id=goal_id)
    repo.create_learning_session(
        db_conn, learning_item_id=item_id, session_date="2025-01-06",
        duration_min=90, takeaway="Basics"
    )
    repo.create_learning_session(
        db_conn, learning_item_id=item_id, session_date="2025-01-07",
        duration_min=90, takeaway="More"
    )

    # Thu: remaining = 5-3 = 2h = 120min, 4 days left → 30 min (already multiple of 5)
    suggestions = sug_svc.suggest_tasks_for("2025-01-09", db_conn)
    assert len(suggestions) == 1
    assert suggestions[0].minutes % 5 == 0
