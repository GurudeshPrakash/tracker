"""Learning page — skills, sessions, history, review.

Layout per spec Section 8.4 with four tabs.
"""

import streamlit as st

st.set_page_config(page_title="Learning | Tracker", page_icon="📚", layout="wide")

from datetime import date as dt_date, timedelta
from lib.dates import today, add_days, week_start, week_end
from lib.ui import format_minutes, status_badge
from db.connection import get_conn
from db import repository as repo
from db.models import RESOURCE_TYPES, LEARNING_ITEM_STATUSES
from services import learning as learn_svc

today_iso = today()

st.title("📚 Learning Tracker")

tab1, tab2, tab3, tab4 = st.tabs(["Skills & Resources", "Log Session", "History", "Review Takeaways"])

# ---------------------------------------------------------------------------
# Tab 1: Skills & Resources
# ---------------------------------------------------------------------------
with tab1:
    st.subheader("Learning Items")

    with get_conn() as conn:
        items = repo.get_all_learning_items(conn)
        goals = repo.get_all_goals(conn)

    if items:
        for item in items:
            cols = st.columns([3, 1, 1, 1, 0.5])
            with cols[0]:
                st.markdown(f"**{item.skill}** — {item.resource}")
            with cols[1]:
                st.caption(item.resource_type)
            with cols[2]:
                st.caption(f"{status_badge(item.status)} {item.status}")
            with cols[3]:
                if item.goal_id:
                    goal = next((g for g in goals if g.id == item.goal_id), None)
                    st.caption(f"🎯 {goal.title}" if goal else "")
            with cols[4]:
                if st.button("✏️", key=f"edit_item_{item.id}"):
                    st.session_state["editing_item"] = item.id
    else:
        st.info("No learning items yet. Add one below!")

    st.markdown("---")
    st.subheader("Add Learning Item")

    with st.form("add_item_form", clear_on_submit=True):
        icols = st.columns([2, 2, 1, 1])
        with icols[0]:
            skill = st.text_input("Skill", placeholder="e.g. SQL")
        with icols[1]:
            resource = st.text_input("Resource", placeholder="e.g. Mode SQL tutorial")
        with icols[2]:
            resource_type = st.selectbox("Type", RESOURCE_TYPES)
        with icols[3]:
            status = st.selectbox("Status", LEARNING_ITEM_STATUSES, index=1)

        goal_options = {"None": None}
        for g in goals:
            goal_options[g.title] = g.id
        selected_goal = st.selectbox("Link to Goal (optional)", list(goal_options.keys()))

        if st.form_submit_button("Add Item", use_container_width=True):
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

        @st.dialog("Edit Learning Item")
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
                selected_g = st.selectbox("Goal", list(goal_opts.keys()),
                    index=list(goal_opts.keys()).index(current_goal_label))

                if st.form_submit_button("Save"):
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
    st.subheader("Log a Study Session")

    with get_conn() as conn:
        items = repo.get_all_learning_items(conn)

    if not items:
        st.warning("Add a learning item first on the 'Skills & Resources' tab.")
    else:
        item_options = {f"{it.skill} — {it.resource}": it.id for it in items}

        with st.form("log_session_form", clear_on_submit=True):
            selected_item = st.selectbox("Learning Item", list(item_options.keys()))
            session_date = st.date_input("Date", value=dt_date.fromisoformat(today_iso))
            duration = st.number_input("Duration (minutes)", min_value=1, value=30, step=5)
            takeaway = st.text_area("What did you learn? (required)",
                placeholder="Write at least a sentence about what you learned")
            confidence = st.slider("Confidence (1-5)", 1, 5, 3)

            if st.form_submit_button("Log Session", use_container_width=True, type="primary"):
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

                        # Show week total for this skill
                        ws = week_start(session_date.isoformat())
                        we = week_end(session_date.isoformat())
                        with get_conn() as conn:
                            totals = learn_svc.totals_by_skill(ws, we, conn)
                        item = items[list(item_options.values()).index(item_options[selected_item])]
                        skill_total = next((t for t in totals if t["skill"] == item.skill), None)
                        week_mins = skill_total["minutes"] if skill_total else duration

                        st.success(
                            f"✅ Session logged! "
                            f"Total for {item.skill} this week: {format_minutes(week_mins)}"
                        )
                    except ValueError as e:
                        st.error(str(e))
                else:
                    st.error("Takeaway is required! Write what you learned.")

# ---------------------------------------------------------------------------
# Tab 3: History
# ---------------------------------------------------------------------------
with tab3:
    st.subheader("Session History")

    # Filters
    filter_cols = st.columns([1, 1, 1, 2])
    with filter_cols[0]:
        with get_conn() as conn:
            all_skills = repo.get_distinct_skills(conn)
        skill_filter = st.selectbox("Skill", ["All"] + all_skills)

    with filter_cols[1]:
        start_date = st.date_input("From", value=dt_date.fromisoformat(today_iso) - timedelta(days=30))

    with filter_cols[2]:
        end_date = st.date_input("To", value=dt_date.fromisoformat(today_iso))

    with filter_cols[3]:
        search_query = st.text_input("Search takeaways", placeholder="Search...")

    # Fetch sessions
    with get_conn() as conn:
        if search_query.strip():
            sessions = repo.search_takeaways(conn, search_query.strip())
        elif skill_filter != "All":
            sessions = repo.get_sessions_in_range(conn, start_date.isoformat(),
                end_date.isoformat(), skill=skill_filter)
        else:
            sessions = repo.get_sessions_in_range(conn, start_date.isoformat(),
                end_date.isoformat())

        # Get items for display
        items_map = {}
        for s in sessions:
            if s.learning_item_id not in items_map:
                item = repo.get_learning_item(conn, s.learning_item_id)
                items_map[s.learning_item_id] = item

    if sessions:
        for session in sessions:
            item = items_map.get(session.learning_item_id)
            with st.container():
                cols = st.columns([1, 2, 1, 1])
                with cols[0]:
                    st.caption(session.session_date)
                with cols[1]:
                    skill_name = item.skill if item else "Unknown"
                    st.markdown(f"**{skill_name}** — {format_minutes(session.duration_min)}")
                with cols[2]:
                    if session.confidence:
                        st.caption(f"Confidence: {'⭐' * session.confidence}")
                with cols[3]:
                    pass
                st.markdown(f"> {session.takeaway}")
                st.markdown("---")
    else:
        st.info("No sessions found for the selected filters.")

# ---------------------------------------------------------------------------
# Tab 4: Review Takeaways (spaced repetition light)
# ---------------------------------------------------------------------------
with tab4:
    st.subheader("🧠 Review Past Takeaways")
    st.caption("Random takeaways from more than 7 days ago. Do you still remember?")

    seven_days_ago = add_days(today_iso, -7)
    with get_conn() as conn:
        old_takeaways = repo.get_random_old_takeaways(conn, seven_days_ago, limit=5)

    if old_takeaways:
        for i, tw in enumerate(old_takeaways):
            with st.container():
                st.markdown(f"**{tw['skill']}** — {tw['resource']}")
                st.caption(f"Studied on {tw['session_date']}")
                st.info(tw['takeaway'])
                cols = st.columns(2)
                with cols[0]:
                    st.button("✅ Still remember", key=f"remember_{i}")
                with cols[1]:
                    st.button("❌ Forgot", key=f"forgot_{i}")
                st.markdown("---")
    else:
        st.info("No old takeaways to review yet. Keep studying for at least a week!")
