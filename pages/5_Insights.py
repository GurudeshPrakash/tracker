"""Insights page — charts and metrics.

Layout per spec Section 8.6. Handles empty data gracefully.
Modernized with dark theme Plotly visuals, glassmorphism summary cards, and range toggles.
"""

import streamlit as st

st.set_page_config(page_title="Insights | Tracker", page_icon="📊", layout="wide")

from lib.ui import inject_custom_css, render_metric_card, format_minutes
inject_custom_css()

from datetime import date as dt_date, timedelta
import plotly.express as px
from lib.dates import today
from db.connection import get_conn
from db import repository as repo
from services import stats

today_iso = today()

st.markdown(
    """
    <h1 style="margin: 0; padding: 0;">📊 Performance & Momentum Insights</h1>
    <div style="color: #94a3b8; font-size: 0.95rem; margin-top: 0.2rem; margin-bottom: 1.25rem;">
        Analytical breakdowns of execution completion, learning investments, and energy ratings.
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Date range selector
# ---------------------------------------------------------------------------
range_options = {
    "Last 7 days": 7,
    "Last 30 days": 30,
    "Last 90 days": 90,
    "Custom": None,
}

c_sel, _ = st.columns([2, 4])
with c_sel:
    selected_range = st.selectbox("Select Window", list(range_options.keys()))

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

m1, m2, m3, m4 = st.columns(4)
with m1:
    render_metric_card("Update Streak", f"{streak}d", "Consecutive day close-outs", "🔥")
with m2:
    rating_val = f"{avg_rat:.1f} / 5.0" if avg_rat else "—"
    render_metric_card("Average Rating", rating_val, "Daily satisfaction score", "⭐")
with m3:
    render_metric_card("Total Focused Study", format_minutes(total_study), f"{start_str} to {end_str}", "📚")
with m4:
    render_metric_card("Tasks Completed", str(tasks_completed), "Finished todo items", "✅")

st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------
chart_theme = {
    "paper_bgcolor": "rgba(0,0,0,0)",
    "plot_bgcolor": "rgba(0,0,0,0)",
    "font": {"color": "#94a3b8", "family": "Plus Jakarta Sans, sans-serif"},
}

row1_c1, row1_c2 = st.columns(2)

with row1_c1:
    st.markdown("<h3>📈 Completion Rate per Day</h3>", unsafe_allow_html=True)
    with get_conn() as conn:
        cr_df = stats.completion_rate_series(start_str, end_str, conn)

    if not cr_df.empty:
        fig = px.line(cr_df, x="date", y="rate", markers=True,
                      labels={"rate": "Completion %", "date": "Date"},
                      color_discrete_sequence=["#10b981"])
        fig.update_layout(yaxis_range=[0, 100], **chart_theme)
        fig.update_xaxes(showgrid=False)
        fig.update_yaxes(gridcolor="rgba(255,255,255,0.06)")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No day close-outs yet. Complete days in Daily Update to view your completion trend.")

with row1_c2:
    st.markdown("<h3>⏱️ Time Investment by Category</h3>", unsafe_allow_html=True)
    with get_conn() as conn:
        cat_df = stats.minutes_by_category(start_str, end_str, conn)

    if not cat_df.empty:
        fig = px.bar(cat_df, x="category", y="minutes",
                     color="category",
                     color_discrete_map={"work": "#3b82f6", "learning": "#8b5cf6", "personal": "#14b8a6"},
                     labels={"minutes": "Minutes", "category": "Category"})
        fig.update_layout(**chart_theme)
        fig.update_xaxes(showgrid=False)
        fig.update_yaxes(gridcolor="rgba(255,255,255,0.06)")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No completed tasks with recorded duration in this date range.")

row2_c1, row2_c2 = st.columns(2)

with row2_c1:
    st.markdown("<h3>📚 Study Time by Skill</h3>", unsafe_allow_html=True)
    with get_conn() as conn:
        skill_df = stats.study_minutes_by_skill(start_str, end_str, conn)

    if not skill_df.empty:
        fig = px.bar(skill_df, x="skill", y="minutes",
                     color="skill",
                     color_discrete_sequence=["#6366f1", "#a855f7", "#ec4899", "#3b82f6"],
                     labels={"minutes": "Minutes", "skill": "Skill"})
        fig.update_layout(**chart_theme)
        fig.update_xaxes(showgrid=False)
        fig.update_yaxes(gridcolor="rgba(255,255,255,0.06)")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No study sessions logged for this period.")

with row2_c2:
    st.markdown("<h3>⭐ Day Rating Trend</h3>", unsafe_allow_html=True)
    with get_conn() as conn:
        updates = repo.get_daily_updates_in_range(conn, start_str, end_str)

    rated_updates = [u for u in updates if u.day_rating is not None]
    if rated_updates:
        import pandas as pd
        rating_data = pd.DataFrame([
            {"date": u.date, "rating": u.day_rating} for u in rated_updates
        ])
        fig = px.line(rating_data, x="date", y="rating", markers=True,
                      labels={"rating": "Rating (1-5)", "date": "Date"},
                      color_discrete_sequence=["#f59e0b"])
        fig.update_layout(yaxis_range=[0, 5.5], **chart_theme)
        fig.update_xaxes(showgrid=False)
        fig.update_yaxes(gridcolor="rgba(255,255,255,0.06)")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No daily satisfaction ratings logged yet.")

# 12-Week Rolling Study Time
st.markdown("<h3>📅 12-Week Rolling Study Trajectory</h3>", unsafe_allow_html=True)
with get_conn() as conn:
    week_df = stats.study_minutes_per_week(12, today_iso, conn)

if not week_df.empty and week_df["minutes"].sum() > 0:
    fig = px.bar(week_df, x="week_start", y="minutes",
                 labels={"minutes": "Study Minutes", "week_start": "Week Commencing"},
                 color_discrete_sequence=["#6366f1"])
    fig.update_layout(**chart_theme)
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="rgba(255,255,255,0.06)")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Study minutes will be compiled automatically as you log sessions over time.")
