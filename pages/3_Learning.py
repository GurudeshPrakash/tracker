"""Learning page — skills, sessions, history, review.

Layout per spec Section 8.4 with four tabs.
Modernized with glassmorphism, visual skill badges, and spaced repetition card review.
"""

import streamlit as st

st.set_page_config(page_title="Learning | Tracker", page_icon="📚", layout="wide")

from lib.ui import inject_custom_css, format_minutes, status_badge, render_pill
inject_custom_css()

from datetime import date as dt_date, timedelta
from lib.dates import today, add_days, week_start, week_end
from db.connection import get_conn
from db import repository as repo
from db.models import RESOURCE_TYPES, LEARNING_ITEM_STATUSES
from services import learning as learn_svc

today_iso = today()

st.markdown(
    """
    <h1 style="margin: 0; padding: 0;">📚 Continuous Mastery Hub</h1>
    <div style="color: #94a3b8; font-size: 0.95rem; margin-top: 0.2rem; margin-bottom: 1.25rem;">
        Deliberate study tracking, deep-dive takeaways, and spaced repetition recall.
    </div>
    """,
    unsafe_allow_html=True,
)

tab1, tab2, tab3, tab4 = st.tabs(["🎯 Skills & Resources", "⏱️ Log Session", "📜 Study History", "🧠 Spaced Review"])

# ---------------------------------------------------------------------------
# Tab 1: Skills & Resources
# ---------------------------------------------------------------------------
with tab1:
    with get_conn() as conn:
        items = repo.get_all_learning_items(conn)
        goals = repo.get_all_goals(conn)

    st.markdown("<h3>Curated Learning Items</h3>", unsafe_allow_html=True)
    if items:
        for item in items:
            with st.container():
                cols = st.columns([3.5, 1.2, 1.2, 1.5, 0.6])
                with cols[0]:
                    st.markdown(
                        f"<div style='font-size: 1rem; font-weight: 700; color: #f8fafc;'>{item.skill}</div>"
                        f"<div style='font-size: 0.85rem; color: #94a3b8;'>{item.resource}</div>",
                        unsafe_allow_html=True,
                    )
                with cols[1]:
                    st.markdown(render_pill(item.resource_type.capitalize(), "work"), unsafe_allow_html=True)
                with cols[2]:
                    stat_type = "low" if item.status == "in_progress" else "medium"
                    st.markdown(render_pill(item.status.replace('_', ' ').capitalize(), stat_type), unsafe_allow_html=True)
                with cols[3]:
                    if item.goal_id:
                        goal = next((g for g in goals if g.id == item.goal_id), None)
                        if goal:
                            st.markdown(f"<span style='color: #818cf8; font-size: 0.85rem; font-weight: 600;'>🎯 {goal.title}</span>", unsafe_allow_html=True)
                with cols[4]:
                    if st.button("✏️", key=f"edit_item_{item.id}", help="Edit item"):
                        st.session_state["editing_item"] = item.id
                st.markdown("<hr style='border-color: rgba(255,255,255,0.06); margin: 0.5rem 0;'>", unsafe_allow_html=True)
    else:
        st.info("No learning resources added yet. Define a skill and resource below to begin tracking.")

    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
    st.markdown("<h3>➕ Add Learning Resource</h3>", unsafe_allow_html=True)

    with st.form("add_item_form", clear_on_submit=True):
        icols = st.columns([2.5, 2.5, 1.5, 1.5])
        with icols[0]:
            skill = st.text_input("Skill Category", placeholder="e.g. Python System Design, Docker")
        with icols[1]:
            resource = st.text_input("Resource / Course", placeholder="e.g. Designing Data-Intensive Applications")
        with icols[2]:
            resource_type = st.selectbox("Resource Medium", RESOURCE_TYPES)
        with icols[3]:
            status = st.selectbox("Current Status", LEARNING_ITEM_STATUSES, index=1)

        goal_options = {"None": None}
        for g in goals:
            goal_options[g.title] = g.id
        selected_goal = st.selectbox("Link to Objective / Goal (Optional)", list(goal_options.keys()))

        if st.form_submit_button("＋ Save Learning Item", use_container_width=True, type="primary"):
            if skill.strip() and resource.strip():
                with get_conn() as conn:
                    repo.create_learning_item(
                        conn,
                        skill=skill.strip(),
                        resource=resource.strip(),
                        resource_type=resource_type,
                        status=status,
                        goal_id=goal_options[selected_goal],
                    )
                st.rerun()
            else:
                st.error("Skill and Resource are required.")

    # Edit item dialog
    if "editing_item" in st.session_state:
        edit_id = st.session_state["editing_item"]

        @st.dialog("✏️ Edit Learning Resource")
        def edit_item_dialog():
            with get_conn() as conn:
                item = repo.get_learning_item(conn, edit_id)
            if not item:
                st.error("Item not found")
                return

            with st.form("edit_item"):
                skill = st.text_input("Skill", value=item.skill)
                resource = st.text_input("Resource", value=item.resource)
                resource_type = st.selectbox("Type", RESOURCE_TYPES,
                    index=RESOURCE_TYPES.index(item.resource_type))
                status = st.selectbox("Status", LEARNING_ITEM_STATUSES,
                    index=LEARNING_ITEM_STATUSES.index(item.status))

                goal_opts = {"None": None}
                for g in goals:
                    goal_opts[g.title] = g.id
                current_goal_label = "None"
                if item.goal_id:
                    for label, gid in goal_opts.items():
                        if gid == item.goal_id:
                            current_goal_label = label
                            break
                selected_g = st.selectbox("Linked Goal", list(goal_opts.keys()),
                    index=list(goal_opts.keys()).index(current_goal_label))

                if st.form_submit_button("Save Changes", type="primary", use_container_width=True):
                    with get_conn() as conn:
                        repo.update_learning_item(conn, edit_id,
                            skill=skill, resource=resource,
                            resource_type=resource_type, status=status,
                            goal_id=goal_opts[selected_g])
                    del st.session_state["editing_item"]
                    st.rerun()

        edit_item_dialog()

# ---------------------------------------------------------------------------
# Tab 2: Log Session
# ---------------------------------------------------------------------------
with tab2:
    st.markdown("<h3>⏱️ Record Study Session</h3>", unsafe_allow_html=True)

    with get_conn() as conn:
        items = repo.get_all_learning_items(conn)

    if not items:
        st.warning("Please add at least one learning item on the 'Skills & Resources' tab first.")
    else:
        item_options = {f"{it.skill} — {it.resource}": it.id for it in items}

        with st.form("log_session_form", clear_on_submit=True):
            col_sel, col_d, col_dur = st.columns([3, 1.5, 1.5])
            with col_sel:
                selected_item = st.selectbox("Learning Item", list(item_options.keys()))
            with col_d:
                session_date = st.date_input("Session Date", value=dt_date.fromisoformat(today_iso))
            with col_dur:
                duration = st.number_input("Duration (minutes)", min_value=1, value=30, step=5)

            takeaway = st.text_area("Key Takeaway / Breakthrough (Required)",
                placeholder="What did you understand, implement, or remember from this session?", height=120)
            confidence = st.slider("Retention Confidence ⭐ (1: Struggling - 5: Mastered)", 1, 5, 3)

            if st.form_submit_button("💾 Log Study Session", use_container_width=True, type="primary"):
                if takeaway.strip():
                    try:
                        with get_conn() as conn:
                            session_id = learn_svc.log_session(
                                item_id=item_options[selected_item],
                                session_date=session_date.isoformat(),
                                duration_min=duration,
                                takeaway=takeaway.strip(),
                                confidence=confidence,
                                conn=conn,
                            )

                        ws = week_start(session_date.isoformat())
                        we = week_end(session_date.isoformat())
                        with get_conn() as conn:
                            totals = learn_svc.totals_by_skill(ws, we, conn)
                        item = items[list(item_options.values()).index(item_options[selected_item])]
                        skill_total = next((t for t in totals if t["skill"] == item.skill), None)
                        week_mins = skill_total["minutes"] if skill_total else duration

                        st.success(
                            f"🎉 Session saved! Total focused time for **{item.skill}** this week: **{format_minutes(week_mins)}**"
                        )
                    except ValueError as e:
                        st.error(str(e))
                else:
                    st.error("A takeaway is required! Condense your learning into at least one key point.")

# ---------------------------------------------------------------------------
# Tab 3: History
# ---------------------------------------------------------------------------
with tab3:
    st.markdown("<h3>📜 Historical Sessions</h3>", unsafe_allow_html=True)

    filter_cols = st.columns([1.5, 1, 1, 2])
    with filter_cols[0]:
        with get_conn() as conn:
            all_skills = repo.get_distinct_skills(conn)
        skill_filter = st.selectbox("Filter Skill", ["All"] + all_skills)

    with filter_cols[1]:
        start_date = st.date_input("From Date", value=dt_date.fromisoformat(today_iso) - timedelta(days=30))

    with filter_cols[2]:
        end_date = st.date_input("To Date", value=dt_date.fromisoformat(today_iso))

    with filter_cols[3]:
        search_query = st.text_input("Search Takeaways", placeholder="Keyword search...")

    with get_conn() as conn:
        if search_query.strip():
            sessions = repo.search_takeaways(conn, search_query.strip())
        elif skill_filter != "All":
            sessions = repo.get_sessions_in_range(conn, start_date.isoformat(),
                end_date.isoformat(), skill=skill_filter)
        else:
            sessions = repo.get_sessions_in_range(conn, start_date.isoformat(),
                end_date.isoformat())

        items_map = {}
        for s in sessions:
            if s.learning_item_id not in items_map:
                item = repo.get_learning_item(conn, s.learning_item_id)
                items_map[s.learning_item_id] = item

    if sessions:
        for session in sessions:
            item = items_map.get(session.learning_item_id)
            skill_name = item.skill if item else "Unknown"
            resource_name = item.resource if item else ""
            stars = "⭐" * session.confidence if session.confidence else ""

            st.markdown(
                f"""
                <div class="tracker-card" style="margin-bottom: 0.75rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.4rem;">
                        <div>
                            <span style="font-weight: 700; color: #f8fafc; font-size: 1rem;">{skill_name}</span>
                            <span style="color: #94a3b8; font-size: 0.85rem; margin-left: 0.5rem;">({resource_name})</span>
                        </div>
                        <div>
                            <span style="background: rgba(99, 102, 241, 0.15); color: #a5b4fc; padding: 0.2rem 0.6rem; border-radius: 9999px; font-size: 0.8rem; font-weight: 600;">
                                ⏱️ {format_minutes(session.duration_min)}
                            </span>
                            <span style="color: #64748b; font-size: 0.8rem; margin-left: 0.5rem;">{session.session_date}</span>
                        </div>
                    </div>
                    <div style="background: rgba(0, 0, 0, 0.2); border-left: 3px solid #6366f1; padding: 0.6rem 0.9rem; border-radius: 4px 8px 8px 4px; color: #e2e8f0; font-size: 0.92rem; margin-top: 0.4rem;">
                        "{session.takeaway}"
                    </div>
                    <div style="margin-top: 0.4rem; font-size: 0.8rem; color: #94a3b8;">
                        Confidence: <span style="letter-spacing: 2px;">{stars}</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.info("No study sessions match the active criteria.")

# ---------------------------------------------------------------------------
# Tab 4: Review Takeaways (Spaced Repetition Light)
# ---------------------------------------------------------------------------
with tab4:
    st.markdown("<h3>🧠 Spaced Repetition Recall</h3>", unsafe_allow_html=True)
    st.caption("Active recall: Revisit concepts learned more than 7 days ago to consolidate memory into long-term retention.")

    seven_days_ago = add_days(today_iso, -7)
    with get_conn() as conn:
        old_takeaways = repo.get_random_old_takeaways(conn, seven_days_ago, limit=5)

    if old_takeaways:
        for i, tw in enumerate(old_takeaways):
            st.markdown(
                f"""
                <div class="tracker-card">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 0.4rem;">
                        <span style="font-weight: 700; color: #818cf8;">{tw['skill']}</span>
                        <span style="color: #64748b; font-size: 0.8rem;">Logged: {tw['session_date']}</span>
                    </div>
                    <div style="font-size: 0.85rem; color: #94a3b8; margin-bottom: 0.5rem;">Resource: {tw['resource']}</div>
                    <div style="background: rgba(255, 255, 255, 0.03); border: 1px dashed rgba(255, 255, 255, 0.1); border-radius: 10px; padding: 1rem; color: #f1f5f9; font-size: 1rem; margin-bottom: 0.75rem;">
                        {tw['takeaway']}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            cols = st.columns([1, 1, 4])
            with cols[0]:
                st.button("✅ Still Recall", key=f"remember_{i}", use_container_width=True)
            with cols[1]:
                st.button("❌ Need Refresh", key=f"forgot_{i}", use_container_width=True)
            st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)
    else:
        st.info("No takeaways older than 7 days yet. As your sessions age, active recall cards will automatically appear here!")
