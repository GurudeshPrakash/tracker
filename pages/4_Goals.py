"""Goals page — goal management with progress tracking.

Layout per spec Section 8.5.
"""

import streamlit as st

st.set_page_config(page_title="Goals | Tracker", page_icon="🎯", layout="wide")

from datetime import date as dt_date
from lib.dates import today
from lib.ui import status_badge, format_minutes
from db.connection import get_conn
from db import repository as repo
from db.models import GOAL_TARGET_TYPES, GOAL_STATUSES
from services import goals as goal_svc
from services import suggestions as suggest_svc
from services import tasks as task_svc

today_iso = today()

st.title("🎯 Goals")

# ---------------------------------------------------------------------------
# Goal list as cards
# ---------------------------------------------------------------------------
with get_conn() as conn:
    all_goals = repo.get_all_goals(conn)

if all_goals:
    for goal in all_goals:
        with get_conn() as conn:
            progress = goal_svc.goal_progress(goal.id, today_iso, conn)
            linked_items = repo.get_all_learning_items(conn)
            linked = [it for it in linked_items if it.goal_id == goal.id]

        with st.container():
            # Header
            cols = st.columns([3, 1, 1])
            with cols[0]:
                st.subheader(f"{goal.title}")
            with cols[1]:
                st.caption(f"{status_badge(progress['status'])} {progress['status']}")
            with cols[2]:
                st.caption(f"{goal.target_type.replace('_', ' ').title()}")

            # Progress bar
            pct = min(progress["percent"], 100) / 100
            st.progress(pct)

            # Stats
            stat_cols = st.columns(4)
            with stat_cols[0]:
                st.metric("Done", f"{progress['done_hours']:.1f}h")
            with stat_cols[1]:
                st.metric("This Week", f"{progress['week_hours']:.1f}h")
            with stat_cols[2]:
                st.metric("Target", f"{goal.target_hours}h")
            with stat_cols[3]:
                st.metric("Progress", f"{progress['percent']:.0f}%")

            if progress["expected_percent"] is not None:
                st.caption(f"Expected pace: {progress['expected_percent']:.0f}%")

            # Linked resources
            if linked:
                with st.expander("📚 Linked Resources"):
                    for it in linked:
                        st.markdown(f"• **{it.skill}** — {it.resource} ({it.status})")

            # Actions
            action_cols = st.columns(4)
            with action_cols[0]:
                if goal.status == "active" and st.button("✅ Mark Done", key=f"gdone_{goal.id}"):
                    with get_conn() as conn:
                        repo.update_goal(conn, goal.id, status="done")
                    st.rerun()
            with action_cols[1]:
                if goal.status == "active" and st.button("⏸️ Pause", key=f"gpause_{goal.id}"):
                    with get_conn() as conn:
                        repo.update_goal(conn, goal.id, status="paused")
                    st.rerun()
            with action_cols[2]:
                if goal.status == "paused" and st.button("▶️ Resume", key=f"gresume_{goal.id}"):
                    with get_conn() as conn:
                        repo.update_goal(conn, goal.id, status="active")
                    st.rerun()
            with action_cols[3]:
                if goal.status in ("active", "paused") and st.button("🗑️ Drop", key=f"gdrop_{goal.id}"):
                    with get_conn() as conn:
                        repo.update_goal(conn, goal.id, status="dropped")
                    st.rerun()

            # Suggestion for behind goals
            if progress["status"] == "behind":
                with get_conn() as conn:
                    suggestions = suggest_svc.suggest_tasks_for(today_iso, conn)
                goal_sugs = [s for s in suggestions if s.goal_id == goal.id]
                for sug in goal_sugs:
                    st.warning(f"💡 **{sug.title}** — {sug.reason}")
                    if st.button("Add to today", key=f"sug_add_{goal.id}"):
                        with get_conn() as conn:
                            task_svc.create_task(
                                conn,
                                title=sug.title,
                                planned_date=today_iso,
                                category="learning",
                                goal_id=goal.id,
                                estimated_min=sug.minutes,
                            )
                        st.rerun()

            st.markdown("---")
else:
    st.info("No goals yet. Add one below!")

# ---------------------------------------------------------------------------
# Add/Edit Goal Form
# ---------------------------------------------------------------------------
st.subheader("➕ Add Goal")

with st.form("add_goal_form", clear_on_submit=True):
    gcols = st.columns([2, 1, 1])
    with gcols[0]:
        title = st.text_input("Goal Title", placeholder="e.g. Learn SQL")
    with gcols[1]:
        target_type = st.selectbox("Type", ["weekly_hours", "total_hours"])
    with gcols[2]:
        target_hours = st.number_input("Target Hours", min_value=0.5, value=5.0, step=0.5)

    dcols = st.columns(2)
    with dcols[0]:
        start_date = st.date_input("Start Date", value=dt_date.fromisoformat(today_iso))
    with dcols[1]:
        target_date = st.date_input("Target Date (for total_hours goals)", value=None)

    if st.form_submit_button("Create Goal", use_container_width=True, type="primary"):
        if title.strip():
            if target_type == "total_hours" and not target_date:
                st.error("Total hours goals require a target date.")
            else:
                with get_conn() as conn:
                    repo.create_goal(
                        conn,
                        title=title.strip(),
                        target_type=target_type,
                        target_hours=target_hours,
                        start_date=start_date.isoformat(),
                        target_date=target_date.isoformat() if target_date else None,
                    )
                st.rerun()
        else:
            st.error("Goal title is required.")
