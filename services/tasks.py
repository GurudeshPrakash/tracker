"""Task service — create, complete, uncomplete, drop, restore, top-3 rules.

All business logic for tasks lives here. This module never imports Streamlit.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from db import repository as repo
from db.models import Task
from lib.dates import today


def create_task(
    conn,
    title: str,
    planned_date: str | None = None,
    due_date: str | None = None,
    priority: str = "medium",
    category: str = "work",
    goal_id: int | None = None,
    learning_item_id: int | None = None,
    parent_task_id: int | None = None,
    estimated_min: int | None = None,
    notes: str | None = None,
) -> int:
    """Create a new task. Defaults planned_date to today if not provided.

    Args:
        conn: Database connection.
        title: Task title (required).
        planned_date: Date to plan the task. None = backlog.
        due_date: Hard deadline (optional).
        priority: 'high', 'medium', or 'low'.
        category: 'work', 'learning', or 'personal'.
        goal_id: Optional linked goal.
        learning_item_id: Optional linked learning item.
        parent_task_id: Optional parent task for subtasks.
        estimated_min: Estimated minutes.
        notes: Additional notes.

    Returns:
        The new task id.
    """
    return repo.create_task(
        conn,
        title=title,
        planned_date=planned_date,
        due_date=due_date,
        priority=priority,
        category=category,
        goal_id=goal_id,
        learning_item_id=learning_item_id,
        parent_task_id=parent_task_id,
        estimated_min=estimated_min,
        notes=notes,
    )


def complete(task_id: int, conn, today_date: str | None = None) -> Task:
    """Mark a task as done.

    Sets status='done', completed_at=now, completed_date=today.
    Raises ValueError if the task has open subtasks.

    Args:
        task_id: The task to complete.
        conn: Database connection.
        today_date: Override for testing. Defaults to today().

    Returns:
        The updated task.
    """
    if today_date is None:
        today_date = today()

    task = repo.get_task(conn, task_id)
    if task is None:
        raise ValueError(f"Task {task_id} not found")

    # Check for open subtasks (Section 7.2)
    open_subs = repo.get_open_subtasks(conn, task_id)
    if open_subs:
        raise ValueError(
            f"Cannot complete task '{task.title}': "
            f"{len(open_subs)} subtask(s) still open"
        )

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    repo.complete_task(conn, task_id, completed_at=now, completed_date=today_date)
    return repo.get_task(conn, task_id)


def uncomplete(task_id: int, conn) -> Task:
    """Revert a done task back to todo.

    Clears completed_at and completed_date.
    """
    repo.uncomplete_task(conn, task_id)
    return repo.get_task(conn, task_id)


def drop(task_id: int, conn) -> None:
    """Soft-delete a task (status='dropped')."""
    repo.drop_task(conn, task_id)


def restore(task_id: int, conn) -> None:
    """Restore a dropped task to todo."""
    repo.restore_task(conn, task_id)


def delete_permanently(task_id: int, conn) -> None:
    """Permanently delete a task."""
    repo.delete_task_permanently(conn, task_id)


def set_top3(task_id: int, value: bool, conn) -> None:
    """Set or clear the top-3 flag.

    Raises ValueError if setting a 4th top-3 task for the same planned_date.
    """
    task = repo.get_task(conn, task_id)
    if task is None:
        raise ValueError(f"Task {task_id} not found")

    if value:
        # Check the limit (Section 7.2): at most 3 top-3 tasks per date
        if task.planned_date:
            current_count = repo.count_top3_todo(conn, task.planned_date)
            # Don't count this task if it's already top-3
            already = task.is_top3 and task.status == "todo"
            effective = current_count - (1 if already else 0)
            if effective >= 3:
                raise ValueError("Only 3 priorities per day")

    repo.set_top3(conn, task_id, 1 if value else 0)


def update_task(task_id: int, conn, **fields) -> None:
    """Update arbitrary fields on a task."""
    repo.update_task(conn, task_id, **fields)


def get_tasks_for_today(conn, today_date: str | None = None) -> dict:
    """Get all task groups for the Today page.

    Returns a dict with:
        top3: list[Task] — top-3 priority tasks
        other_high: list[Task] — high priority, not top-3
        other_medium: list[Task] — medium priority
        other_low: list[Task] — low priority
        completed: list[Task] — completed today
        overdue: list[Task] — overdue tasks
    """
    if today_date is None:
        today_date = today()

    todo_tasks = repo.get_todo_tasks_for_date(conn, today_date)
    completed = repo.get_done_tasks_for_date(conn, today_date)
    overdue = repo.get_overdue_tasks(conn, today_date)

    top3 = [t for t in todo_tasks if t.is_top3]
    other = [t for t in todo_tasks if not t.is_top3]

    return {
        "top3": top3,
        "other_high": [t for t in other if t.priority == "high"],
        "other_medium": [t for t in other if t.priority == "medium"],
        "other_low": [t for t in other if t.priority == "low"],
        "completed": completed,
        "overdue": overdue,
    }
