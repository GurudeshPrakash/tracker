"""Streamlit entry point: startup tasks + modern command center dashboard."""

import streamlit as st

st.set_page_config(page_title="Tracker | Command Center", page_icon="⚡", layout="wide")

from lib.ui import inject_custom_css, render_metric_card, format_minutes
inject_custom_css()

from lib.dates import today, add_days
from db.connection import get_conn
from db.migrations import run_migrations
from services import rollover, stats, backup, recurring
from db import repository as repo
from services import goals as goal_svc


@st.cache_resource
def startup(_today_iso: str):
    """Run once per day: migrations, backup, recurring tasks, rollover."""
    with get_conn() as conn:
        run_migrations(conn)
    with get_conn() as conn:
        backup.auto_backup(_today_iso)
    with get_conn() as conn:
        recurring.generate_for_date(_today_iso, conn)
    with get_conn() as conn:
        rollover.rollover(add_days(_today_iso, -1), _today_iso, conn)
    return True


# Run startup tasks
today_iso = today()
startup(today_iso)

# ---------------------------------------------------------------------------
# Header & Hero Banner
# ---------------------------------------------------------------------------
st.markdown(
    f"""
    <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; margin-bottom: 1.5rem;">
        <div>
            <h1 style="margin: 0; padding: 0;">⚡ Focus Command Center</h1>
            <div style="color: #94a3b8; font-size: 0.95rem; margin-top: 0.25rem;">
                Empower your productivity & continuous mastery &bull; <b>{today_iso}</b>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Fetch metrics
with get_conn() as conn:
    streak = stats.update_streak(today_iso, conn)
    done_today = repo.count_completed_for_date(conn, today_iso)
    todo_tasks = repo.get_todo_tasks_for_date(conn, today_iso)
    planned_today = len(todo_tasks) + done_today
    study_min = repo.study_minutes_for_date(conn, today_iso)

    active_goals = repo.get_active_goals(conn)
    behind_goals = []
    for g in active_goals:
        progress = goal_svc.goal_progress(g.id, today_iso, conn)
        if progress["status"] == "behind":
            behind_goals.append((g, progress))

# Metric Cards Row
c1, c2, c3, c4 = st.columns(4)
with c1:
    render_metric_card("Current Streak", f"{streak}d", "Consecutive days with updates", "🔥")
with c2:
    pct = int((done_today / planned_today) * 100) if planned_today > 0 else 0
    render_metric_card("Tasks Completed", f"{done_today} / {planned_today}", f"{pct}% of today's plan finished", "✅")
with c3:
    render_metric_card("Learning Time", format_minutes(study_min), "Dedicated focused study", "📚")
with c4:
    alert_sub = f"{len(behind_goals)} goals need attention" if behind_goals else "All active goals on schedule!"
    render_metric_card("Goals Behind", str(len(behind_goals)), alert_sub, "🎯")

# Behind goals warning if any
if behind_goals:
    st.markdown(
        """
        <div style="background: rgba(239, 68, 68, 0.08); border: 1px solid rgba(239, 68, 68, 0.25); border-radius: 14px; padding: 1rem 1.25rem; margin: 1.25rem 0;">
            <div style="color: #f87171; font-weight: 700; margin-bottom: 0.4rem; display: flex; align-items: center; gap: 0.5rem;">
                ⚠️ Focus Needed: Active Goals Falling Behind Pace
            </div>
        """,
        unsafe_allow_html=True,
    )
    for g, prog in behind_goals:
        st.markdown(
            f"""
            <div style="color: #cbd5e1; font-size: 0.9rem; padding: 0.2rem 0;">
                &bull; <b style="color: #ffffff;">{g.title}</b>: {prog['done_hours']:.1f}h done of {g.target_hours}h target ({prog['percent']:.0f}% completed)
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div style='height: 1.25rem;'></div>", unsafe_allow_html=True)

# Quick Nav Cards
st.subheader("🚀 Quick Actions")
nav_col1, nav_col2, nav_col3 = st.columns(3)

with nav_col1:
    with st.container():
        st.markdown(
            """
            <div class="tracker-card" style="height: 125px;">
                <div style="font-weight: 700; font-size: 1.1rem; color: #f8fafc; margin-bottom: 0.35rem;">
                    📋 Daily Execution Board
                </div>
                <div style="font-size: 0.85rem; color: #94a3b8;">
                    Manage Top-3 priorities, tackle tasks, and track subtask items for today.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Open Today's Tasks →", key="nav_today", use_container_width=True, type="primary"):
            st.switch_page("pages/1_Today.py")

with nav_col2:
    with st.container():
        st.markdown(
            """
            <div class="tracker-card" style="height: 125px;">
                <div style="font-weight: 700; font-size: 1.1rem; color: #f8fafc; margin-bottom: 0.35rem;">
                    📝 Evening Daily Reflection
                </div>
                <div style="font-size: 0.85rem; color: #94a3b8;">
                    Close out your day, log takeaways, preserve streak, and choose carried tasks.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Open Daily Update →", key="nav_daily", use_container_width=True):
            st.switch_page("pages/2_Daily_Update.py")

with nav_col3:
    with st.container():
        st.markdown(
            """
            <div class="tracker-card" style="height: 125px;">
                <div style="font-weight: 700; font-size: 1.1rem; color: #f8fafc; margin-bottom: 0.35rem;">
                    📚 Skill Mastery & Review
                </div>
                <div style="font-size: 0.85rem; color: #94a3b8;">
                    Log deep study sessions, track resources, and review spaced repetition takeaways.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Explore Learning Hub →", key="nav_learning", use_container_width=True):
            st.switch_page("pages/3_Learning.py")
