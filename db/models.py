"""Domain models as dataclasses.

No ORM — these are plain data containers populated by repository functions.
Enumerations are defined as tuples per spec Section 6.3.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

# ---------------------------------------------------------------------------
# Enumerations (Section 6.3)
# ---------------------------------------------------------------------------
PRIORITIES = ("high", "medium", "low")
CATEGORIES = ("work", "learning", "personal")
TASK_STATUSES = ("todo", "done", "dropped")
RESOURCE_TYPES = ("course", "book", "video", "article", "practice", "project", "other")
LEARNING_ITEM_STATUSES = ("planned", "in_progress", "done", "paused")
GOAL_STATUSES = ("active", "done", "paused", "dropped")
GOAL_TARGET_TYPES = ("weekly_hours", "total_hours")
RECURRING_RULES = ("daily", "weekdays", "weekly", "monthly")


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------
@dataclass
class Task:
    """A single task."""
    id: int
    title: str
    notes: Optional[str] = None
    planned_date: Optional[str] = None
    due_date: Optional[str] = None
    priority: str = "medium"
    category: str = "work"
    goal_id: Optional[int] = None
    learning_item_id: Optional[int] = None
    parent_task_id: Optional[int] = None
    recurring_id: Optional[int] = None
    status: str = "todo"
    is_top3: int = 0
    rollover_count: int = 0
    estimated_min: Optional[int] = None
    actual_min: Optional[int] = None
    completed_at: Optional[str] = None
    completed_date: Optional[str] = None
    created_at: Optional[str] = None


@dataclass
class DailyUpdate:
    """End-of-day summary."""
    id: int
    date: str
    planned_count: int = 0
    completed_count: int = 0
    completed_summary: Optional[str] = None
    learned_today: Optional[str] = None
    study_minutes: int = 0
    day_rating: Optional[int] = None
    blockers: Optional[str] = None
    tomorrow_focus: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class DailyUpdateForm:
    """Form data for closing a day (not stored directly; mapped to DailyUpdate)."""
    completed_summary: str = ""
    learned_today: str = ""
    study_minutes: int = 0
    day_rating: Optional[int] = None
    blockers: str = ""
    tomorrow_focus: str = ""


@dataclass
class LearningItem:
    """A skill/resource being studied."""
    id: int
    skill: str
    resource: str
    resource_type: str = "course"
    status: str = "in_progress"
    goal_id: Optional[int] = None
    created_at: Optional[str] = None


@dataclass
class LearningSession:
    """A single study session."""
    id: int
    learning_item_id: int
    task_id: Optional[int] = None
    session_date: str = ""
    duration_min: int = 0
    takeaway: str = ""
    confidence: Optional[int] = None
    created_at: Optional[str] = None


@dataclass
class Goal:
    """A learning/work goal."""
    id: int
    title: str
    target_type: str = "weekly_hours"
    target_hours: float = 0.0
    start_date: str = ""
    target_date: Optional[str] = None
    status: str = "active"
    created_at: Optional[str] = None


@dataclass
class RecurringTask:
    """A recurring task template."""
    id: int
    title: str
    priority: str = "medium"
    category: str = "work"
    goal_id: Optional[int] = None
    learning_item_id: Optional[int] = None
    estimated_min: Optional[int] = None
    rule: str = "daily"
    weekday: Optional[int] = None
    day_of_month: Optional[int] = None
    start_date: str = ""
    end_date: Optional[str] = None
    active: int = 1
    last_generated: Optional[str] = None


@dataclass
class Review:
    """Weekly review."""
    id: int
    week_start: str
    wins: Optional[str] = None
    blockers: Optional[str] = None
    next_focus: Optional[str] = None
    created_at: Optional[str] = None


@dataclass
class Suggestion:
    """A suggested task from goals analysis."""
    goal_id: int
    title: str
    minutes: int
    reason: str
