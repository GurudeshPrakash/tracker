"""Daily Update page — end-of-day close-out.

Layout per spec Section 8.3.
"""

import streamlit as st

st.set_page_config(page_title="Daily Update | Tracker", page_icon="📝", layout="wide")

from datetime import date as dt_date
from lib.dates import today, add_days
from lib.ui import format_minutes
from db.connection import get_conn
from db import repository as repo
from db.models import DailyUpdateForm
from services import daily_update as du_svc
from services import suggestions as suggest_svc

today_iso = today()

st.title("📝 Daily Update")

# ---------------------------------------------------------------------------
# Date selector (default today, allow past days)
# ---------------------------------------------------------------------------
selected_date = st.date_input("Date", value=dt_date.fromisoformat(today_iso))
date_str = selected_date.isoformat()

# ---------------------------------------------------------------------------
# Build prefill
# ---------------------------------------------------------------------------
with get_conn() as conn:
    prefill = du_svc.build_prefill(date_str, conn)

completed_tasks = prefill["completed_tasks"]
open_tasks = prefill["open_tasks"]
study_minutes = prefill["study_minutes"]
session_takeaways = prefill["session_takeaways"]
existing = prefill["existing"]

is_already_closed = existing is not None

# ---------------------------------------------------------------------------
# Summary panel
# ---------------------------------------------------------------------------
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("✅ Completed", len(completed_tasks))
with col2:
    st.metric("⬜ Still Open", len(open_tasks))
with col3:
    st.metric("📚 Study Minutes", format_minutes(study_minutes))

if is_already_closed:
    st.info("ℹ️ This day has already been closed. You can edit text fields below, but rollover has already happened.")

st.markdown("---")

# ---------------------------------------------------------------------------
# Form
# ---------------------------------------------------------------------------
# Pre-fill values
default_summary = "\n".join([f"• {t.title}" for t in completed_tasks])
default_learned = "\n".join([f"• {tw}" for tw in session_takeaways])

if existing:
    default_summary = existing.completed_summary or default_summary
    default_learned = existing.learned_today or default_learned
    default_study_min = existing.study_minutes
    default_rating = existing.day_rating
    default_blockers = existing.blockers or ""
    default_focus = existing.tomorrow_focus or ""
else:
    default_study_min = study_minutes
    default_rating = None
    default_blockers = ""
    default_focus = ""

with st.form("daily_update_form"):
    completed_summary = st.text_area(
        "What I completed today",
        value=default_summary,
        height=120,
    )

    learned_today = st.text_area(
        "What I learned today",
        value=default_learned,
        height=100,
    )

    study_min_input = st.number_input(
        "Study minutes",
        min_value=0,
        value=default_study_min,
        step=5,
    )

    day_rating = st.slider(
        "Day rating ⭐",
        min_value=1,
        max_value=5,
        value=default_rating or 3,
    )

    blockers = st.text_area(
        "Blockers",
        value=default_blockers,
        placeholder="What got in your way?",
    )

    tomorrow_focus = st.text_input(
        "Tomorrow's focus",
        value=default_focus,
        placeholder="What's most important tomorrow?",
    )

    # Open tasks — carry to tomorrow (Section 8.3)
    if open_tasks and not is_already_closed:
        st.subheader("Open Tasks")
        st.caption("Checked = carry to tomorrow. Unchecked = drop.")

        carry_selections = {}
        for task in open_tasks:
            carry_selections[task.id] = st.checkbox(
                f"{task.title}",
                value=True,
                key=f"carry_{task.id}",
            )

    # Submit
    if is_already_closed:
        submit_label = "Update"
    else:
        submit_label = "Close Day and Plan Tomorrow"

    submitted = st.form_submit_button(submit_label, use_container_width=True, type="primary")

    if submitted:
        form = DailyUpdateForm(
            completed_summary=completed_summary,
            learned_today=learned_today,
            study_minutes=study_min_input,
            day_rating=day_rating,
            blockers=blockers,
            tomorrow_focus=tomorrow_focus,
        )

        if is_already_closed:
            # Just update text fields, no rollover
            with get_conn() as conn:
                planned_count = existing.planned_count
                completed_count = existing.completed_count
                repo.upsert_daily_update(
                    conn,
                    date=date_str,
                    planned_count=planned_count,
                    completed_count=completed_count,
                    completed_summary=form.completed_summary,
                    learned_today=form.learned_today,
                    study_minutes=form.study_minutes,
                    day_rating=form.day_rating,
                    blockers=form.blockers,
                    tomorrow_focus=form.tomorrow_focus,
                )
            st.success("✅ Update saved!")
        else:
            carry_ids = []
            if open_tasks:
                carry_ids = [tid for tid, checked in carry_selections.items() if checked]

            with get_conn() as conn:
                du_svc.close_day(date_str, form, carry_ids, conn)

            st.success("✅ Day closed! Unfinished tasks have been moved to tomorrow.")
            st.balloons()

            # Show tomorrow's tasks
            next_day = add_days(date_str, 1)
            st.subheader(f"📋 Tomorrow ({next_day})")
            with get_conn() as conn:
                tomorrow_tasks = repo.get_todo_tasks_for_date(conn, next_day)
                suggestions = suggest_svc.suggest_tasks_for(next_day, conn)

            if tomorrow_tasks:
                for t in tomorrow_tasks:
                    st.markdown(f"• {t.title}")
            else:
                st.info("No tasks planned yet.")

            if suggestions:
                st.subheader("💡 Suggestions for tomorrow")
                for sug in suggestions:
                    st.markdown(f"• **{sug.title}** — {sug.reason}")
