"""Daily Update page — end-of-day close-out.

Layout per spec Section 8.3. Modernized with glassmorphism and clear decision controls.
"""

import streamlit as st

st.set_page_config(page_title="Daily Update | Tracker", page_icon="📝", layout="wide")

from lib.ui import inject_custom_css, render_metric_card, format_minutes, render_pill
inject_custom_css()

from datetime import date as dt_date
from lib.dates import today, add_days
from db.connection import get_conn
from db import repository as repo
from db.models import DailyUpdateForm
from services import daily_update as du_svc
from services import suggestions as suggest_svc

today_iso = today()

# ---------------------------------------------------------------------------
# Header & Date Selector
# ---------------------------------------------------------------------------
col_head, col_date = st.columns([3, 1])
with col_head:
    st.markdown(
        """
        <h1 style="margin: 0; padding: 0;">📝 Evening Daily Reflection</h1>
        <div style="color: #94a3b8; font-size: 0.95rem; margin-top: 0.2rem;">
            Log takeaways, evaluate your focus, maintain streaks, and plan tomorrow.
        </div>
        """,
        unsafe_allow_html=True,
    )
with col_date:
    selected_date = st.date_input("Select Date to Close", value=dt_date.fromisoformat(today_iso))
    date_str = selected_date.isoformat()

st.markdown("<div style='height: 0.75rem;'></div>", unsafe_allow_html=True)

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

# Summary metrics row
c1, c2, c3 = st.columns(3)
with c1:
    render_metric_card("Tasks Finished", str(len(completed_tasks)), f"{date_str} completed items", "✅")
with c2:
    render_metric_card("Unfinished Tasks", str(len(open_tasks)), "Items requiring rollover decision", "⏳")
with c3:
    render_metric_card("Study Logged", format_minutes(study_minutes), "Focused learning recorded", "📚")

if is_already_closed:
    st.info("ℹ️ This day has already been closed. You can edit reflections and ratings below without re-triggering rollover.")

st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Form
# ---------------------------------------------------------------------------
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
    st.markdown("<div style='font-size: 1.15rem; font-weight: 700; color: #f8fafc; margin-bottom: 0.5rem;'>📋 Reflection & Daily Insights</div>", unsafe_allow_html=True)

    completed_summary = st.text_area(
        "What I completed today",
        value=default_summary,
        height=110,
        placeholder="List accomplishments...",
    )

    learned_today = st.text_area(
        "Key takeaways & discoveries",
        value=default_learned,
        height=100,
        placeholder="What new concept or insight did you uncover today?",
    )

    col_m, col_r = st.columns(2)
    with col_m:
        study_min_input = st.number_input(
            "Study duration (minutes)",
            min_value=0,
            value=default_study_min,
            step=5,
        )
    with col_r:
        day_rating = st.slider(
            "Day Satisfaction & Energy ⭐ (1-5)",
            min_value=1,
            max_value=5,
            value=default_rating or 3,
        )

    col_b, col_f = st.columns(2)
    with col_b:
        blockers = st.text_area(
            "Obstacles & Blockers",
            value=default_blockers,
            placeholder="Did anything stall or distract you?",
            height=85,
        )
    with col_f:
        tomorrow_focus = st.text_area(
            "Primary Focus for Tomorrow",
            value=default_focus,
            placeholder="What 1-2 major outcomes matter most tomorrow?",
            height=85,
        )

    # Open tasks — carry to tomorrow (Section 8.3)
    carry_selections = {}
    if open_tasks and not is_already_closed:
        st.markdown(
            """
            <div style='margin-top: 1rem;'>
                <div style='font-size: 1.1rem; font-weight: 700; color: #f8fafc;'>⏳ Unfinished Tasks Disposition</div>
                <div style='font-size: 0.85rem; color: #94a3b8; margin-bottom: 0.5rem;'>
                    Checked tasks will safely roll over to tomorrow. Unchecked tasks will be marked as dropped.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        for task in open_tasks:
            col_check, col_tag = st.columns([4, 1])
            with col_check:
                carry_selections[task.id] = st.checkbox(
                    f"{task.title}",
                    value=True,
                    key=f"carry_{task.id}",
                )
            with col_tag:
                st.markdown(render_pill(task.priority.capitalize(), task.priority), unsafe_allow_html=True)

    st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)

    submit_label = "💾 Save Reflection Changes" if is_already_closed else "🌙 Close My Day & Carry Forward to Tomorrow"
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
            st.success("✅ Daily update reflections saved successfully!")
        else:
            carry_ids = [tid for tid, checked in carry_selections.items() if checked]
            with get_conn() as conn:
                du_svc.close_day(date_str, form, carry_ids, conn)

            st.success("🎉 Day officially closed! Rollover completed.")
            st.balloons()

            next_day = add_days(date_str, 1)
            st.markdown(f"### 📋 Tomorrow's Board Preview ({next_day})")
            with get_conn() as conn:
                tomorrow_tasks = repo.get_todo_tasks_for_date(conn, next_day)
                suggestions = suggest_svc.suggest_tasks_for(next_day, conn)

            if tomorrow_tasks:
                for t in tomorrow_tasks:
                    st.markdown(f"&bull; **{t.title}** ({t.priority.capitalize()})")
            else:
                st.info("No tasks carried over.")

            if suggestions:
                st.markdown("#### 💡 Suggestions queued for tomorrow")
                for sug in suggestions:
                    st.markdown(f"&bull; **{sug.title}** — *{sug.reason}*")
