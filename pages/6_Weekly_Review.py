"""Weekly Review page — auto-filled summary and reflection form.

Layout per spec Section 8.7.
"""

import streamlit as st

st.set_page_config(page_title="Weekly Review | Tracker", page_icon="📅", layout="wide")

from datetime import date as dt_date
from lib.dates import today, week_start, add_days
from lib.ui import format_minutes, rating_stars
from db.connection import get_conn
from db import repository as repo
from services import stats

today_iso = today()
current_week = week_start(today_iso)

st.title("📅 Weekly Review")

# ---------------------------------------------------------------------------
# Week selector
# ---------------------------------------------------------------------------
weeks = []
for i in range(12):
    ws = add_days(current_week, -7 * i)
    weeks.append(ws)

selected_week = st.selectbox("Select Week", weeks,
    format_func=lambda w: f"Week of {w}")

# ---------------------------------------------------------------------------
# Auto-filled summary (read-only cards)
# ---------------------------------------------------------------------------
with get_conn() as conn:
    summary = stats.week_summary(selected_week, conn)

st.subheader("📊 Week Summary")

cols = st.columns(4)
with cols[0]:
    st.metric("✅ Tasks Completed", summary["tasks_completed"])
with cols[1]:
    st.metric("📈 Completion Rate", f"{summary['completion_rate']:.0f}%")
with cols[2]:
    st.metric("📚 Study Hours", f"{summary['study_hours']:.1f}h")
with cols[3]:
    st.metric("⭐ Avg Rating", f"{summary['avg_rating']:.1f}" if summary["avg_rating"] else "—")

# Additional info
info_cols = st.columns(3)
with info_cols[0]:
    if summary["best_day"]:
        bd = summary["best_day"]
        st.info(f"🏆 **Best Day:** {bd['date']} (Rating: {bd['rating']}, {bd['completed']} tasks)")
    else:
        st.info("🏆 **Best Day:** No ratings this week")

with info_cols[1]:
    st.info(f"📚 **Top Skill:** {summary['top_skill'] or 'No study sessions'}")

with info_cols[2]:
    if summary["blockers"]:
        st.warning(f"🚧 **Blockers:** {len(summary['blockers'])} day(s) had blockers")
    else:
        st.success("🚧 **No Blockers** reported this week")

# Takeaways
if summary["takeaways"]:
    with st.expander(f"📝 Takeaways ({len(summary['takeaways'])})"):
        for tw in summary["takeaways"]:
            st.markdown(f"• {tw}")

st.markdown("---")

# ---------------------------------------------------------------------------
# Review form (Section 8.7)
# ---------------------------------------------------------------------------
st.subheader("✍️ Weekly Reflection")

with get_conn() as conn:
    existing_review = repo.get_review(conn, selected_week)

with st.form("review_form"):
    wins = st.text_area("🎉 Wins",
        value=existing_review.wins if existing_review else "",
        placeholder="What went well this week?",
        height=100)

    blockers = st.text_area("🚧 Blockers",
        value=existing_review.blockers if existing_review else "",
        placeholder="What held you back?",
        height=100)

    next_focus = st.text_area("🎯 Next Week's Focus",
        value=existing_review.next_focus if existing_review else "",
        placeholder="What's most important next week?",
        height=100)

    if st.form_submit_button("Save Review", use_container_width=True, type="primary"):
        with get_conn() as conn:
            repo.upsert_review(conn, selected_week,
                wins=wins or None,
                blockers=blockers or None,
                next_focus=next_focus or None)
        st.success("✅ Review saved!")

# ---------------------------------------------------------------------------
# Past reviews
# ---------------------------------------------------------------------------
st.markdown("---")
st.subheader("📜 Past Reviews")

with get_conn() as conn:
    all_reviews = repo.get_all_reviews(conn)

past_reviews = [r for r in all_reviews if r.week_start != selected_week]

if past_reviews:
    for rev in past_reviews[:10]:
        with st.expander(f"Week of {rev.week_start}"):
            if rev.wins:
                st.markdown(f"**🎉 Wins:** {rev.wins}")
            if rev.blockers:
                st.markdown(f"**🚧 Blockers:** {rev.blockers}")
            if rev.next_focus:
                st.markdown(f"**🎯 Focus:** {rev.next_focus}")
else:
    st.info("No past reviews yet.")
