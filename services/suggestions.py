"""Suggestions service — rule-based task suggestions for goals.

Rules from spec Section 7.7. Suggestions are never auto-created.
"""

from __future__ import annotations

import math
import sqlite3

from db import repository as repo
from db.models import Suggestion
from services.goals import goal_progress
from lib.dates import week_end, days_between


def suggest_tasks_for(date: str, conn: sqlite3.Connection) -> list[Suggestion]:
    """Generate task suggestions for a given date based on active goals.

    Rules (Section 7.7):
    - For each active goal, compute remaining hours and daily minutes needed.
    - Only suggest if the goal is 'behind' OR minutes > 0 and no task for
      that goal is already planned for the date.
    - Cap minutes at 180, round up to nearest 5.
    - Title: "Study {skill or goal title} ({minutes} min)"
    - Reason: "Behind on '{goal}': {done}h of {target}h"

    Returns:
        List of Suggestion dataclasses.
    """
    active_goals = repo.get_active_goals(conn)
    suggestions = []

    for goal in active_goals:
        progress = goal_progress(goal.id, date, conn)

        # Skip completed or paused/dropped goals
        if progress["status"] == "complete":
            continue
        if goal.status != "active":
            continue

        # Check if a task for this goal is already planned for the date
        existing_tasks = repo.get_tasks_for_goal_on_date(conn, goal.id, date)
        if existing_tasks:
            continue

        # Calculate minutes needed
        if goal.target_type == "weekly_hours":
            remaining_h = max(0, goal.target_hours - progress["week_hours"])
            # Days left from date to Sunday inclusive
            we = week_end(date)
            days_left = max(1, days_between(date, we) + 1)
            minutes = math.ceil(remaining_h * 60 / days_left)
        else:  # total_hours
            remaining_h = max(0, goal.target_hours - progress["done_hours"])
            if goal.target_date:
                days_left = max(1, days_between(date, goal.target_date) + 1)
            else:
                days_left = 1
            minutes = math.ceil(remaining_h * 60 / days_left)

        # Only suggest if behind or there's work to do
        if progress["status"] != "behind" and minutes <= 0:
            continue

        if minutes <= 0:
            minutes = 30  # Minimum suggestion

        # Cap at 180 and round up to nearest 5
        minutes = min(minutes, 180)
        minutes = math.ceil(minutes / 5) * 5

        title = f"Study {goal.title} ({minutes} min)"
        reason = (
            f"Behind on '{goal.title}': "
            f"{progress['done_hours']:.1f}h of {goal.target_hours}h"
        )

        suggestions.append(Suggestion(
            goal_id=goal.id,
            title=title,
            minutes=minutes,
            reason=reason,
        ))

    return suggestions
