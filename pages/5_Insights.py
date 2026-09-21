"""Insights page — charts and metrics.

Layout per spec Section 8.6. Handles empty data gracefully.
"""

import streamlit as st

st.set_page_config(page_title="Insights | Tracker", page_icon="📊", layout="wide")

from datetime import date as dt_date, timedelta
import plotly.express as px
from lib.dates import today, add_days
from lib.ui import format_minutes, rating_stars
from db.connection import get_conn
from db import repository as repo
from services import stats

today_iso = today()

st.title("📊 Insights")

# ---------------------------------------------------------------------------
# Date range selector
# ---------------------------------------------------------------------------
range_options = {
    "Last 7 days": 7,
    "Last 30 days": 30,
    "Last 90 days": 90,
    "Custom": None,
}

selected_range = st.selectbox("Date Range", list(range_options.keys()))

if selected_range == "Custom":
    col_s, col_e = st.columns(2)
    with col_s:
        start_date = st.date_input("Start", value=dt_date.fromisoformat(today_iso) - timedelta(days=30))
    with col_e:
        end_date = st.date_input("End", value=dt_date.fromisoformat(today_iso))
else:
    days = range_options[selected_range]
    end_date = dt_date.fromisoformat(today_iso)
    start_date = end_date - timedelta(days=days)

start_str = start_date.isoformat()
end_str = end_date.isoformat()

# ---------------------------------------------------------------------------
# Metrics row
# ---------------------------------------------------------------------------
with get_conn() as conn:
    streak = stats.update_streak(today_iso, conn)
    avg_rat = stats.average_rating(start_str, end_str, conn)
    total_study = conn.execute(
        "SELECT COALESCE(SUM(duration_min), 0) FROM learning_session WHERE session_date BETWEEN ? AND ?",
        (start_str, end_str),
    ).fetchone()[0]
    tasks_completed = repo.count_done_tasks_in_range(conn, start_str, end_str)

mcols = st.columns(4)
with mcols[0]:
    st.metric("🔥 Update Streak", f"{streak} day{'s' if streak != 1 else ''}")
with mcols[1]:
    st.metric("⭐ Avg Rating", f"{avg_rat:.1f}" if avg_rat else "—")
with mcols[2]:
    st.metric("📚 Total Study", format_minutes(total_study))
with mcols[3]:
    st.metric("✅ Tasks Completed", tasks_completed)

st.markdown("---")

# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------

# 1. Completion rate per day
st.subheader("📈 Completion Rate per Day")
with get_conn() as conn:
    cr_df = stats.completion_rate_series(start_str, end_str, conn)

if not cr_df.empty:
    fig = px.line(cr_df, x="date", y="rate", markers=True,
                  labels={"rate": "Completion %", "date": "Date"},
                  color_discrete_sequence=["#4CAF50"])
    fig.update_layout(yaxis_range=[0, 100])
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No data yet. Close some days to see your completion rate.")

# 2. Time by category
st.subheader("⏱️ Time by Category")
with get_conn() as conn:
    cat_df = stats.minutes_by_category(start_str, end_str, conn)

if not cat_df.empty:
    fig = px.bar(cat_df, x="category", y="minutes",
                 color="category",
                 color_discrete_map={"work": "#2196F3", "learning": "#FF9800", "personal": "#9C27B0"},
                 labels={"minutes": "Minutes", "category": "Category"})
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No completed tasks with tracked time yet.")

# 3. Study minutes by skill
st.subheader("📚 Study Minutes by Skill")
with get_conn() as conn:
    skill_df = stats.study_minutes_by_skill(start_str, end_str, conn)

if not skill_df.empty:
    fig = px.bar(skill_df, x="skill", y="minutes",
                 color="skill",
                 labels={"minutes": "Minutes", "skill": "Skill"})
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No study sessions logged yet.")

# 4. Study minutes per week
st.subheader("📅 Study Minutes per Week")
with get_conn() as conn:
    week_df = stats.study_minutes_per_week(12, today_iso, conn)

if not week_df.empty and week_df["minutes"].sum() > 0:
    fig = px.bar(week_df, x="week_start", y="minutes",
                 labels={"minutes": "Minutes", "week_start": "Week Starting"},
                 color_discrete_sequence=["#FF9800"])
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No study data for the last 12 weeks.")

# 5. Day rating trend
st.subheader("⭐ Day Rating Trend")
with get_conn() as conn:
    updates = repo.get_daily_updates_in_range(conn, start_str, end_str)

rated_updates = [u for u in updates if u.day_rating is not None]
if rated_updates:
    import pandas as pd
    rating_data = pd.DataFrame([
        {"date": u.date, "rating": u.day_rating} for u in rated_updates
    ])
    fig = px.line(rating_data, x="date", y="rating", markers=True,
                  labels={"rating": "Rating", "date": "Date"},
                  color_discrete_sequence=["#FFC107"])
    fig.update_layout(yaxis_range=[0, 6])
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No day ratings yet. Rate your days in the Daily Update.")
