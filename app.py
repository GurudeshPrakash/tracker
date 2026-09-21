"""Streamlit entry point: startup tasks + home dashboard."""

import streamlit as st

st.set_page_config(page_title="Tracker", page_icon="✅", layout="wide")

from lib.dates import today, add_days
from db.connection import get_conn
from db.migrations import run_migrations
from services import rollover, stats
from services import backup
from services import recurring


@st.cache_resource
def startup(_today_iso: str):
    """Run once per day: migrations, backup, recurring tasks, rollover.

    Passing the date as the cache key means startup re-runs after midnight.
    """
    with get_conn() as conn:
        run_migrations(conn)
    with get_conn() as conn:
        backup.auto_backup(_today_iso)
    with get_conn() as conn:
        recurring.generate_for_date(_today_iso, conn)
    with get_conn() as conn:
        rollover.rollover(add_days(_today_iso, -1), _today_iso, conn)
    return True


# Run startup
today_iso = today()
startup(today_iso)

# ---------------------------------------------------------------------------
# Home Dashboard
# ---------------------------------------------------------------------------
st.title("✅ Daily Work & Self-Learning Tracker")
st.markdown(f"### 📅 {today_iso}")

# Dashboard metrics
col1, col2, col3, col4 = st.columns(4)

with get_conn() as conn:
    # Streak
    streak = stats.update_streak(today_iso, conn)

    # Tasks done today vs planned
    from db import repository as repo
    done_today = repo.count_completed_for_date(conn, today_iso)
    planned_today = len(repo.get_todo_tasks_for_date(conn, today_iso)) + done_today

    # Study minutes today
    study_min = repo.study_minutes_for_date(conn, today_iso)

    # Behind goals
    from services import goals as goal_svc
    active_goals = repo.get_active_goals(conn)
    behind_goals = []
    for g in active_goals:
        progress = goal_svc.goal_progress(g.id, today_iso, conn)
        if progress["status"] == "behind":
            behind_goals.append((g, progress))

with col1:
    st.metric("🔥 Streak", f"{streak} day{'s' if streak != 1 else ''}")

with col2:
    st.metric("✅ Done Today", f"{done_today} / {planned_today}")

with col3:
    from lib.ui import format_minutes
    st.metric("📚 Study Today", format_minutes(study_min))

with col4:
    st.metric("🎯 Behind Goals", len(behind_goals))

# Behind goals warning
if behind_goals:
    st.markdown("---")
    st.subheader("⚠️ Goals Behind Schedule")
    for g, prog in behind_goals:
        st.warning(
            f"**{g.title}**: {prog['done_hours']:.1f}h / {g.target_hours}h "
            f"({prog['percent']:.0f}%)"
        )

st.markdown("---")

# Navigation hint
st.info("👈 Use the sidebar to navigate between pages, or click below to get started.")

col_a, col_b, col_c = st.columns(3)
with col_a:
    if st.button("📋 Plan Today", use_container_width=True):
        st.switch_page("pages/1_Today.py")
with col_b:
    if st.button("📝 Daily Update", use_container_width=True):
        st.switch_page("pages/2_Daily_Update.py")
with col_c:
    if st.button("📚 Learning", use_container_width=True):
        st.switch_page("pages/3_Learning.py")
