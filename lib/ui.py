"""Shared Streamlit UI helpers.

Badges, formatters, custom styling injection, and reusable UI components.
"""

from __future__ import annotations

import os
import streamlit as st


def inject_custom_css():
    """Inject modern styling from style.css."""
    css_path = os.path.join(os.path.dirname(__file__), "style.css")
    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as f:
            css = f.read()
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


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


def render_pill(label: str, pill_type: str) -> str:
    """Render an HTML pill badge with matching CSS classes."""
    return f'<span class="badge-pill pill-{pill_type}">{label}</span>'


def render_metric_card(title: str, value: str, subtext: str = "", icon: str = ""):
    """Render a modern glassmorphic summary card."""
    sub_html = f'<div style="font-size:0.8rem; color:#94a3b8; margin-top:0.35rem;">{subtext}</div>' if subtext else ""
    icon_html = f'<span style="font-size:1.3rem; margin-right:0.4rem;">{icon}</span>' if icon else ""
    html = f"""
    <div class="tracker-card" style="margin-bottom: 0.5rem;">
        <div style="font-size: 0.8rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; color: #94a3b8;">
            {icon_html}{title}
        </div>
        <div style="font-size: 1.85rem; font-weight: 800; color: #f8fafc; letter-spacing: -0.02em; margin-top: 0.25rem;">
            {value}
        </div>
        {sub_html}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
