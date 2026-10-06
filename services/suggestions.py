"""Suggestions service — rule-based task suggestions for goals.

Rules from spec Section 7.7. Suggestions are never auto-created.
"""

from __future__ import annotations

import math
import sqlite3

from db import repository as repo
from db.models import Suggestion, Goal
from services.goals import goal_progress
from lib.dates import week_end, days_between


def _calculate_goal_minutes(goal: Goal, progress: dict, date: str) -> int:
    """Calculate raw daily minutes needed for a goal based on target type."""
    if goal.target_type == "weekly_hours":
        remaining_h = max(0, goal.target_hours - progress["week_hours"])
        we = week_end(date)
        days_left = max(1, days_between(date, we) + 1)
        return math.ceil(remaining_h * 60 / days_left)

    remaining_h = max(0, goal.target_hours - progress["done_hours"])
    days_left = max(1, days_between(date, goal.target_date) + 1) if goal.target_date else 1
    return math.ceil(remaining_h * 60 / days_left)


def _build_suggestion(goal: Goal, progress: dict, minutes: int) -> Suggestion:
    """Create a formatted suggestion dataclass with rounded minutes."""
    effective_min = 30 if minutes <= 0 else min(minutes, 180)
    effective_min = math.ceil(effective_min / 5) * 5
    title = f"Study {goal.title} ({effective_min} min)"
    reason = (
        f"Behind on '{goal.title}': "
        f"{progress['done_hours']:.1f}h of {goal.target_hours}h"
    )
    return Suggestion(
        goal_id=goal.id,
        title=title,
        minutes=effective_min,
        reason=reason,
    )


def suggest_tasks_for(date: str, conn: sqlite3.Connection, user_id: int | None = None) -> list[Suggestion]:
    """Generate task suggestions for a given date based on active goals."""
    active_goals = repo.get_active_goals(conn, user_id=user_id)
    suggestions = []

    for goal in active_goals:
        if goal.status != "active":
            continue

        progress = goal_progress(goal.id, date, conn)
        if progress["status"] == "complete":
            continue

        # Check if a task for this goal is already planned for the date
        if repo.get_tasks_for_goal_on_date(conn, goal.id, date, user_id=user_id):
            continue

        minutes = _calculate_goal_minutes(goal, progress, date)
        if progress["status"] != "behind" and minutes <= 0:
            continue

        suggestions.append(_build_suggestion(goal, progress, minutes))

    return suggestions
