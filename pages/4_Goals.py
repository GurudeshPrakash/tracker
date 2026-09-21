"""Goals page — goal management with progress tracking.

Layout per spec Section 8.5. Modernized with progress cards, pacing indicators, and quick actions.
"""

import streamlit as st

st.set_page_config(page_title="Goals | Tracker", page_icon="🎯", layout="wide")

from lib.ui import inject_custom_css, status_badge, format_minutes, render_pill
inject_custom_css()

from datetime import date as dt_date
from lib.dates import today
from db.connection import get_conn
from db import repository as repo
from db.models import GOAL_TARGET_TYPES, GOAL_STATUSES
from services import goals as goal_svc
from services import suggestions as suggest_svc
from services import tasks as task_svc

today_iso = today()

st.markdown(
    """
    <h1 style="margin: 0; padding: 0;">🎯 Strategic Goals & Objectives</h1>
    <div style="color: #94a3b8; font-size: 0.95rem; margin-top: 0.2rem; margin-bottom: 1.25rem;">
        Monitor target hours, weekly learning milestones, and pace tracking.
    </div>
    """,
    unsafe_allow_html=True,
)

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

        status_key = progress["status"]
        pill_type = "high" if status_key == "behind" else ("low" if status_key in ("on_track", "ahead") else "work")

        st.markdown(
            f"""
            <div class="tracker-card">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap;">
                    <div>
                        <span style="font-size: 1.2rem; font-weight: 800; color: #f8fafc;">{goal.title}</span>
                        <span style="margin-left: 0.5rem;">{render_pill(status_key.replace('_', ' ').upper(), pill_type)}</span>
                    </div>
                    <div style="color: #94a3b8; font-size: 0.85rem; font-weight: 500;">
                        {goal.target_type.replace('_', ' ').title()} &bull; Target: <b style="color: #f8fafc;">{goal.target_hours}h</b>
                    </div>
                </div>
            """,
            unsafe_allow_html=True,
        )

        # Progress bar
        pct = min(progress["percent"], 100) / 100
        st.progress(pct)

        # Metrics row
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("Total Completed", f"{progress['done_hours']:.1f}h")
        with m2:
            st.metric("This Week", f"{progress['week_hours']:.1f}h")
        with m3:
            st.metric("Target Hours", f"{goal.target_hours}h")
        with m4:
            st.metric("Completion", f"{progress['percent']:.0f}%")

        if progress["expected_percent"] is not None:
            st.caption(f"Target schedule expected pace: **{progress['expected_percent']:.0f}%**")

        # Linked resources
        if linked:
            with st.expander(f"📚 Linked Learning Resources ({len(linked)})", expanded=False):
                for it in linked:
                    st.markdown(f"&bull; **{it.skill}** — *{it.resource}* ({it.status})")

        # Actions row
        col_act1, col_act2, col_act3, col_act4 = st.columns(4)
        with col_act1:
            if goal.status == "active" and st.button("✅ Mark Done", key=f"gdone_{goal.id}", use_container_width=True):
                with get_conn() as conn:
                    repo.update_goal(conn, goal.id, status="done")
                st.rerun()
        with col_act2:
            if goal.status == "active" and st.button("⏸️ Pause", key=f"gpause_{goal.id}", use_container_width=True):
                with get_conn() as conn:
                    repo.update_goal(conn, goal.id, status="paused")
                st.rerun()
        with col_act3:
            if goal.status == "paused" and st.button("▶️ Resume", key=f"gresume_{goal.id}", use_container_width=True):
                with get_conn() as conn:
                    repo.update_goal(conn, goal.id, status="active")
                st.rerun()
        with col_act4:
            if goal.status in ("active", "paused") and st.button("🗑️ Drop Goal", key=f"gdrop_{goal.id}", use_container_width=True):
                with get_conn() as conn:
                    repo.update_goal(conn, goal.id, status="dropped")
                st.rerun()

        # Suggestion for behind goals
        if progress["status"] == "behind":
            with get_conn() as conn:
                suggestions = suggest_svc.suggest_tasks_for(today_iso, conn)
            goal_sugs = [s for s in suggestions if s.goal_id == goal.id]
            for sug in goal_sugs:
                st.warning(f"💡 Recommended Catch-Up: **{sug.title}** ({sug.minutes} min) &bull; *{sug.reason}*")
                if st.button(f"➕ Add to Today's Board", key=f"sug_add_{goal.id}", type="primary"):
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

        st.markdown("</div>", unsafe_allow_html=True)
else:
    st.info("No goals tracked yet. Define your first target below!")

st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Add Goal Form
# ---------------------------------------------------------------------------
st.markdown("<h3>➕ Create New Goal</h3>", unsafe_allow_html=True)

with st.form("add_goal_form", clear_on_submit=True):
    gcols = st.columns([2.5, 1.5, 1.5])
    with gcols[0]:
        title = st.text_input("Goal Title", placeholder="e.g. Master React & State Management")
    with gcols[1]:
        target_type = st.selectbox("Target Cadence", ["weekly_hours", "total_hours"], format_func=lambda x: "Weekly Hours" if x == "weekly_hours" else "Total Milestone Hours")
    with gcols[2]:
        target_hours = st.number_input("Target Hours", min_value=0.5, value=5.0, step=0.5)

    dcols = st.columns(2)
    with dcols[0]:
        start_date = st.date_input("Start Date", value=dt_date.fromisoformat(today_iso))
    with dcols[1]:
        target_date = st.date_input("Target Completion Date (for total hours goals)", value=None)

    if st.form_submit_button("＋ Establish Goal", use_container_width=True, type="primary"):
        if title.strip():
            if target_type == "total_hours" and not target_date:
                st.error("Total hours goals require a target completion date.")
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
            st.error("Goal title cannot be empty.")
