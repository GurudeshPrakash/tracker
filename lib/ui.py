"""Shared Streamlit UI helpers.

Badges, formatters, and reusable UI components.
"""

from __future__ import annotations

import streamlit as st


def priority_badge(priority: str) -> str:
    """Return an emoji badge for a priority level."""
    return {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(priority, "⚪")


def category_badge(category: str) -> str:
    """Return an emoji badge for a category."""
    return {"work": "💼", "learning": "📚", "personal": "🏠"}.get(category, "📌")


def status_badge(status: str) -> str:
    """Return an emoji badge for a status."""
    return {
        "todo": "⬜", "done": "✅", "dropped": "🗑️",
        "active": "🟢", "paused": "⏸️",
        "on_track": "🟢", "behind": "🔴", "ahead": "🚀", "complete": "✅",
        "planned": "📋", "in_progress": "📖",
    }.get(status, "⚪")


def rollover_badge(count: int) -> str:
    """Return a warning badge for rollover count >= 3."""
    if count >= 3:
        return f"⚠️ Rolled over {count}x"
    return ""


def rating_stars(rating: int | None) -> str:
    """Return star display for a 1-5 rating."""
    if rating is None:
        return "—"
    return "⭐" * rating


def format_minutes(minutes: int) -> str:
    """Format minutes as 'Xh Ym' or 'Ym'."""
    if minutes >= 60:
        h = minutes // 60
        m = minutes % 60
        return f"{h}h {m}m" if m else f"{h}h"
    return f"{minutes}m"
