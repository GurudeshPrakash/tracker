"""Weekly Review page — auto-filled summary and reflection form.

Layout per spec Section 8.7. Modernized with glassmorphic cards and intuitive retrospective controls.
"""

import streamlit as st

st.set_page_config(page_title="Weekly Review | Tracker", page_icon="📅", layout="wide")

from lib.ui import inject_custom_css, render_metric_card, format_minutes
inject_custom_css()

from datetime import date as dt_date
from lib.dates import today, week_start, add_days
from db.connection import get_conn
from db import repository as repo
from services import stats

today_iso = today()
current_week = week_start(today_iso)

st.markdown(
    """
    <h1 style="margin: 0; padding: 0;">📅 Weekly Cadence & Retrospective</h1>
    <div style="color: #94a3b8; font-size: 0.95rem; margin-top: 0.2rem; margin-bottom: 1.25rem;">
        Consolidate weekly momentum, acknowledge breakthrough wins, and align upcoming focus.
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Week selector
# ---------------------------------------------------------------------------
weeks = [add_days(current_week, -7 * i) for i in range(12)]
col_s, _ = st.columns([2, 4])
with col_s:
    selected_week = st.selectbox("Select Week Window", weeks, format_func=lambda w: f"Week Commencing {w}")

# ---------------------------------------------------------------------------
# Auto-filled summary
# ---------------------------------------------------------------------------
with get_conn() as conn:
    summary = stats.week_summary(selected_week, conn)

m1, m2, m3, m4 = st.columns(4)
with m1:
    render_metric_card("Tasks Finished", str(summary["tasks_completed"]), "Total completed this week", "✅")
with m2:
    render_metric_card("Completion Ratio", f"{summary['completion_rate']:.0f}%", "Plan vs execution rate", "📈")
with m3:
    render_metric_card("Focused Study", f"{summary['study_hours']:.1f}h", "Total learning logged", "📚")
with m4:
    rat_str = f"{summary['avg_rating']:.1f} / 5" if summary["avg_rating"] else "—"
    render_metric_card("Energy Rating", rat_str, "Weekly average satisfaction", "⭐")

# Highlights row
info_cols = st.columns(3)
with info_cols[0]:
    if summary["best_day"]:
        bd = summary["best_day"]
        st.info(f"🏆 **Peak Day:** {bd['date']} &bull; Rating: {bd['rating']} &bull; {bd['completed']} tasks done")
    else:
        st.info("🏆 **Peak Day:** No ratings recorded this week")

with info_cols[1]:
    top_skill = summary['top_skill'] or 'No sessions logged'
    st.info(f"📚 **Dominant Skill:** {top_skill}")

with info_cols[2]:
    if summary["blockers"]:
        st.warning(f"🚧 **Blockers Flagged:** {len(summary['blockers'])} day(s) encountered blockers")
    else:
        st.success("✨ **Smooth Sailing:** Zero blockers reported this week")

# Takeaways
if summary["takeaways"]:
    with st.expander(f"📝 Weekly Consolidated Takeaways ({len(summary['takeaways'])})", expanded=False):
        for tw in summary["takeaways"]:
            st.markdown(f"&bull; {tw}")

st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Review form
# ---------------------------------------------------------------------------
st.markdown("<h3>✍️ Weekly Reflection & Strategic Alignment</h3>", unsafe_allow_html=True)

with get_conn() as conn:
    existing_review = repo.get_review(conn, selected_week)

with st.form("review_form"):
    wins = st.text_area("🎉 Celebrated Wins & Achievements",
        value=existing_review.wins if existing_review else "",
        placeholder="What breakthroughs, finished projects, or habits succeeded this week?",
        height=100)

    blockers = st.text_area("🚧 Friction, Distractions & Obstacles",
        value=existing_review.blockers if existing_review else "",
        placeholder="What stalled momentum or drained focus?",
        height=100)

    next_focus = st.text_area("🎯 High-Leverage Focus for Next Week",
        value=existing_review.next_focus if existing_review else "",
        placeholder="What single primary outcome will define a successful next week?",
        height=100)

    if st.form_submit_button("💾 Save Weekly Retrospective", use_container_width=True, type="primary"):
        with get_conn() as conn:
            repo.upsert_review(conn, selected_week,
                wins=wins or None,
                blockers=blockers or None,
                next_focus=next_focus or None)
        st.success("✅ Weekly reflection saved successfully!")

# ---------------------------------------------------------------------------
# Past reviews
# ---------------------------------------------------------------------------
st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
st.markdown("<h3>📜 Retrospective Archives</h3>", unsafe_allow_html=True)

with get_conn() as conn:
    all_reviews = repo.get_all_reviews(conn)

past_reviews = [r for r in all_reviews if r.week_start != selected_week]

if past_reviews:
    for rev in past_reviews[:10]:
        with st.expander(f"Retrospective for Week of {rev.week_start}"):
            if rev.wins:
                st.markdown(f"**🎉 Wins:** {rev.wins}")
            if rev.blockers:
                st.markdown(f"**🚧 Blockers:** {rev.blockers}")
            if rev.next_focus:
                st.markdown(f"**🎯 Strategic Focus:** {rev.next_focus}")
else:
    st.info("Past retrospectives will be cataloged here as you review consecutive weeks.")
