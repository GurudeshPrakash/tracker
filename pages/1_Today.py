"""Today page — daily task management.

Layout per spec Section 8.2: header, suggestions, quick add,
top-3, other tasks by priority, completed, overdue, close day button.
Overhauled with modern visual styling and user-friendly interaction patterns.
"""

import streamlit as st

st.set_page_config(page_title="Today | Tracker", page_icon="📋", layout="wide")

from lib.ui import inject_custom_css, render_pill, format_minutes, priority_badge, category_badge, rollover_badge
inject_custom_css()

from lib.dates import today
from db.connection import get_conn
from db import repository as repo
from services import tasks as task_svc
from services import suggestions as suggest_svc

today_iso = today()

# ---------------------------------------------------------------------------
# Header & Progress Bar
# ---------------------------------------------------------------------------
with get_conn() as conn:
    done_count = repo.count_completed_for_date(conn, today_iso)
    todo_tasks = repo.get_todo_tasks_for_date(conn, today_iso)
    planned_count = len(todo_tasks) + done_count

pct = int((done_count / planned_count) * 100) if planned_count > 0 else 0

st.markdown(
    f"""
    <div style="display: flex; align-items: flex-end; justify-content: space-between; flex-wrap: wrap; margin-bottom: 0.75rem;">
        <div>
            <h1 style="margin: 0; padding: 0;">📋 Today's Board</h1>
            <div style="color: #94a3b8; font-size: 0.95rem; margin-top: 0.2rem;">
                Target your priorities & track daily momentum &bull; <b>{today_iso}</b>
            </div>
        </div>
        <div style="text-align: right;">
            <span style="font-size: 1.3rem; font-weight: 800; color: #f8fafc;">{done_count}</span>
            <span style="color: #64748b; font-size: 1rem;"> / {planned_count} Done</span>
            <span style="margin-left: 0.5rem; background: rgba(99, 102, 241, 0.2); color: #818cf8; padding: 0.2rem 0.6rem; border-radius: 9999px; font-weight: 700; font-size: 0.8rem;">{pct}%</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.progress(done_count / planned_count if planned_count > 0 else 0.0)
st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Suggested Tasks (Section 7.7)
# ---------------------------------------------------------------------------
with get_conn() as conn:
    suggestions = suggest_svc.suggest_tasks_for(today_iso, conn)

if suggestions:
    st.markdown(
        """
        <div style="background: rgba(99, 102, 241, 0.07); border: 1px solid rgba(99, 102, 241, 0.2); border-radius: 14px; padding: 1rem 1.25rem; margin-bottom: 1.25rem;">
            <div style="color: #a5b4fc; font-weight: 700; font-size: 0.95rem; margin-bottom: 0.5rem; display: flex; align-items: center; gap: 0.4rem;">
                💡 Recommended Focus (Goal Milestones)
            </div>
        """,
        unsafe_allow_html=True,
    )
    for sug in suggestions:
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(f"<span style='color:#f8fafc; font-weight:600;'>{sug.title}</span> <span style='color:#94a3b8; font-size:0.85rem;'>({format_minutes(sug.minutes)})</span>", unsafe_allow_html=True)
            st.caption(sug.reason)
        with col2:
            if st.button("➕ Add to Today", key=f"add_sug_{sug.goal_id}", use_container_width=True):
                with get_conn() as conn:
                    task_svc.create_task(
                        conn,
                        title=sug.title,
                        planned_date=today_iso,
                        category="learning",
                        goal_id=sug.goal_id,
                        estimated_min=sug.minutes,
                    )
                st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Quick Add (Section 8.2)
# ---------------------------------------------------------------------------
with st.container():
    with st.form("quick_add", clear_on_submit=True):
        st.markdown("<div style='font-size: 1rem; font-weight: 700; color: #f8fafc; margin-bottom: 0.4rem;'>⚡ Quick Add New Task</div>", unsafe_allow_html=True)
        qa_cols = st.columns([3.5, 1.2, 1.2, 1, 1.2])
        with qa_cols[0]:
            new_title = st.text_input("Task Title", placeholder="What do you want to achieve today?", label_visibility="collapsed")
        with qa_cols[1]:
            new_priority = st.selectbox("Priority", ["medium", "high", "low"], label_visibility="collapsed", format_func=lambda x: f"{x.capitalize()} Priority")
        with qa_cols[2]:
            new_category = st.selectbox("Category", ["work", "learning", "personal"], label_visibility="collapsed", format_func=lambda x: f"{x.capitalize()}")
        with qa_cols[3]:
            new_estimate = st.number_input("Est. min", min_value=0, value=0, step=5, label_visibility="collapsed", help="Estimated minutes")
        with qa_cols[4]:
            submitted = st.form_submit_button("＋ Create Task", use_container_width=True, type="primary")

        if submitted and new_title.strip():
            with get_conn() as conn:
                task_svc.create_task(
                    conn,
                    title=new_title.strip(),
                    planned_date=today_iso,
                    priority=new_priority,
                    category=new_category,
                    estimated_min=new_estimate if new_estimate > 0 else None,
                )
            st.rerun()

st.markdown("<div style='height: 1.25rem;'></div>", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Helpers for rendering task rows
# ---------------------------------------------------------------------------
def _render_task_row(task, conn_getter, is_top3_section=False):
    """Render a modern task card row with checkbox, tags, and action buttons."""
    cols = st.columns([0.4, 4.2, 1.1, 1.1, 0.9, 0.5, 0.5, 0.5])

    with cols[0]:
        done = st.checkbox("✓", value=False, key=f"done_{task.id}", label_visibility="collapsed")
        if done:
            with conn_getter() as conn:
                try:
                    task_svc.complete(task.id, conn, today_iso)
                    if task.category == "learning":
                        st.session_state[f"log_session_{task.id}"] = True
                except ValueError as e:
                    st.error(str(e))
            st.rerun()

    with cols[1]:
        notes_badge = " <span style='color:#94a3b8; font-size:0.8rem;' title='Has notes'>📝</span>" if task.notes else ""
        st.markdown(
            f"<span style='font-size: 1rem; font-weight: 600; color: #f8fafc;'>{task.title}</span>{notes_badge}",
            unsafe_allow_html=True,
        )

        # Rollover warning badge
        if task.rollover_count >= 3:
            st.markdown(
                f"<span class='badge-pill pill-rollover'>⚠️ Rolled over {task.rollover_count}x</span>",
                unsafe_allow_html=True,
            )

        # Subtasks
        with conn_getter() as conn:
            subtasks = repo.get_subtasks(conn, task.id)
        if subtasks:
            for sub in subtasks:
                sub_icon = "✅" if sub.status == "done" else "⬜"
                st.caption(f"&nbsp;&nbsp;&nbsp;&bull; {sub_icon} {sub.title}")

    with cols[2]:
        st.markdown(render_pill(task.priority.capitalize(), task.priority), unsafe_allow_html=True)

    with cols[3]:
        st.markdown(render_pill(task.category.capitalize(), task.category), unsafe_allow_html=True)

    with cols[4]:
        if task.estimated_min:
            st.markdown(f"<span style='color:#94a3b8; font-size:0.85rem;'>⏱️ {format_minutes(task.estimated_min)}</span>", unsafe_allow_html=True)

    with cols[5]:
        is_top3 = bool(task.is_top3)
        star = "⭐" if is_top3 else "☆"
        star_help = "Remove from Top 3" if is_top3 else "Mark as Top 3 Priority"
        if st.button(star, key=f"star_{task.id}", help=star_help):
            with conn_getter() as conn:
                try:
                    task_svc.set_top3(task.id, not is_top3, conn)
                except ValueError as e:
                    st.error(str(e))
            st.rerun()

    with cols[6]:
        if st.button("✏️", key=f"edit_{task.id}", help="Edit Task"):
            st.session_state["editing_task"] = task.id

    with cols[7]:
        if st.button("🗑️", key=f"drop_{task.id}", help="Drop Task"):
            with conn_getter() as conn:
                task_svc.drop(task.id, conn)
            st.rerun()

    # Rollover warning action options (Section 7.3)
    if task.rollover_count >= 3:
        rc = st.columns([2, 1, 1, 1])
        with rc[0]:
            st.caption("Stalled task? Choose an action:")
        with rc[1]:
            if st.button("🔨 Subtasks", key=f"break_{task.id}", use_container_width=True):
                st.session_state["adding_subtask_to"] = task.id
        with rc[2]:
            if st.button("📅 Reschedule", key=f"resched_{task.id}", use_container_width=True):
                st.session_state["rescheduling_task"] = task.id
        with rc[3]:
            if st.button("❌ Drop", key=f"rdrop_{task.id}", use_container_width=True):
                with conn_getter() as conn:
                    task_svc.drop(task.id, conn)
                st.rerun()


# ---------------------------------------------------------------------------
# Top 3 Priorities
# ---------------------------------------------------------------------------
with get_conn() as conn:
    top3 = repo.get_top3_tasks(conn, today_iso)

st.markdown(
    """
    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.6rem;">
        <h2 style="margin: 0; padding: 0; display: flex; align-items: center; gap: 0.5rem;">
            🌟 Top 3 Priorities
        </h2>
        <span style="font-size: 0.85rem; color: #fbbf24; font-weight: 600;">Daily Core Focus (Max 3)</span>
    </div>
    """,
    unsafe_allow_html=True,
)

if top3:
    st.markdown('<div class="top3-highlight-card">', unsafe_allow_html=True)
    for task in top3:
        _render_task_row(task, get_conn, is_top3_section=True)
    st.markdown('</div>', unsafe_allow_html=True)
else:
    st.info("💡 No Top-3 priorities set yet. Click the ⭐ icon on your most vital tasks to anchor them here.")

st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Other Tasks by Priority
# ---------------------------------------------------------------------------
with get_conn() as conn:
    all_todo = repo.get_todo_tasks_for_date(conn, today_iso)

other_tasks = [t for t in all_todo if not t.is_top3 and t.parent_task_id is None]

if other_tasks:
    st.markdown("<h2>📋 Planned Tasks</h2>", unsafe_allow_html=True)
    for priority_label, priority_key, border_color in [
        ("🔴 High Priority", "high", "rgba(239, 68, 68, 0.4)"),
        ("🟡 Medium Priority", "medium", "rgba(245, 158, 11, 0.4)"),
        ("🟢 Low Priority", "low", "rgba(16, 185, 129, 0.4)"),
    ]:
        tasks_in_group = [t for t in other_tasks if t.priority == priority_key]
        if tasks_in_group:
            st.markdown(f"<h3 style='margin-top: 1rem;'>{priority_label} ({len(tasks_in_group)})</h3>", unsafe_allow_html=True)
            for task in tasks_in_group:
                _render_task_row(task, get_conn)

# ---------------------------------------------------------------------------
# Completed Today
# ---------------------------------------------------------------------------
with get_conn() as conn:
    completed = repo.get_done_tasks_for_date(conn, today_iso)

if completed:
    with st.expander(f"✅ Completed Today ({len(completed)})", expanded=False):
        for task in completed:
            cols = st.columns([0.4, 4.5, 1.2, 1.2])
            with cols[0]:
                undone = st.checkbox("✓", value=True, key=f"undone_{task.id}", label_visibility="collapsed")
                if not undone:
                    with get_conn() as conn:
                        task_svc.uncomplete(task.id, conn)
                    st.rerun()
            with cols[1]:
                st.markdown(f"<span style='text-decoration: line-through; color: #94a3b8;'>{task.title}</span>", unsafe_allow_html=True)
            with cols[2]:
                st.markdown(render_pill(task.category.capitalize(), task.category), unsafe_allow_html=True)
            with cols[3]:
                if task.actual_min:
                    st.caption(f"⏱️ {format_minutes(task.actual_min)}")

# ---------------------------------------------------------------------------
# Overdue Tasks
# ---------------------------------------------------------------------------
with get_conn() as conn:
    overdue = repo.get_overdue_tasks(conn, today_iso)

if overdue:
    with st.expander(f"⚠️ Overdue Deadlines ({len(overdue)})", expanded=True):
        for task in overdue:
            st.warning(f"**{task.title}** — Due: {task.due_date} &bull; Priority: {task.priority.capitalize()}")

st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Close Day Button CTA
# ---------------------------------------------------------------------------
if st.button("🌙 Close My Day & Log Reflections →", use_container_width=True, type="primary"):
    st.switch_page("pages/2_Daily_Update.py")

# ---------------------------------------------------------------------------
# Edit Task Dialog
# ---------------------------------------------------------------------------
if "editing_task" in st.session_state:
    task_id = st.session_state["editing_task"]

    @st.dialog("✏️ Edit Task Details")
    def edit_dialog():
        with get_conn() as conn:
            task = repo.get_task(conn, task_id)
        if not task:
            st.error("Task not found")
            return

        with st.form("edit_form"):
            title = st.text_input("Title", value=task.title)
            notes = st.text_area("Notes", value=task.notes or "")
            col_p, col_c = st.columns(2)
            with col_p:
                priority = st.selectbox("Priority", ["high", "medium", "low"],
                                         index=["high", "medium", "low"].index(task.priority))
            with col_c:
                category = st.selectbox("Category", ["work", "learning", "personal"],
                                         index=["work", "learning", "personal"].index(task.category))
            due_date = st.date_input("Due date", value=None)
            estimated = st.number_input("Estimated minutes", min_value=0,
                                         value=task.estimated_min or 0, step=5)

            if st.form_submit_button("Save Changes", type="primary", use_container_width=True):
                with get_conn() as conn:
                    task_svc.update_task(task_id, conn,
                        title=title,
                        notes=notes or None,
                        priority=priority,
                        category=category,
                        due_date=str(due_date) if due_date else None,
                        estimated_min=estimated if estimated > 0 else None,
                    )
                del st.session_state["editing_task"]
                st.rerun()

    edit_dialog()

# ---------------------------------------------------------------------------
# Add Subtask Dialog
# ---------------------------------------------------------------------------
if "adding_subtask_to" in st.session_state:
    parent_id = st.session_state["adding_subtask_to"]

    @st.dialog("🔨 Break Down Task into Subtasks")
    def subtask_dialog():
        with get_conn() as conn:
            parent = repo.get_task(conn, parent_id)
        if not parent:
            st.error("Parent task not found")
            return

        st.markdown(f"Parent Task: <b style='color:#6366f1;'>{parent.title}</b>", unsafe_allow_html=True)

        with st.form("subtask_form"):
            sub_title = st.text_input("Subtask title", placeholder="What smaller step is next?")
            if st.form_submit_button("Add Subtask", type="primary", use_container_width=True):
                if sub_title.strip():
                    with get_conn() as conn:
                        task_svc.create_task(
                            conn,
                            title=sub_title.strip(),
                            planned_date=today_iso,
                            priority=parent.priority,
                            category=parent.category,
                            parent_task_id=parent_id,
                        )
                    del st.session_state["adding_subtask_to"]
                    st.rerun()

    subtask_dialog()

# ---------------------------------------------------------------------------
# Reschedule Dialog
# ---------------------------------------------------------------------------
if "rescheduling_task" in st.session_state:
    resched_id = st.session_state["rescheduling_task"]

    @st.dialog("📅 Reschedule Task")
    def reschedule_dialog():
        with get_conn() as conn:
            task = repo.get_task(conn, resched_id)
        if not task:
            st.error("Task not found")
            return

        st.markdown(f"Task: <b style='color:#f8fafc;'>{task.title}</b>", unsafe_allow_html=True)
        new_date = st.date_input("Pick new target date")

        if st.button("Confirm Reschedule", type="primary", use_container_width=True):
            with get_conn() as conn:
                task_svc.update_task(resched_id, conn, planned_date=str(new_date))
            del st.session_state["rescheduling_task"]
            st.rerun()

    reschedule_dialog()

# ---------------------------------------------------------------------------
# Log Study Session Dialog (after completing a learning task)
# ---------------------------------------------------------------------------
for key in list(st.session_state.keys()):
    if key.startswith("log_session_") and st.session_state[key]:
        session_task_id = int(key.split("_")[-1])

        @st.dialog("📚 Log Study Session")
        def session_dialog():
            with get_conn() as conn:
                task = repo.get_task(conn, session_task_id)
                items = repo.get_all_learning_items(conn)

            if not items:
                st.warning("No learning items found. Add one on the Learning page first.")
                if st.button("Skip"):
                    del st.session_state[key]
                    st.rerun()
                return

            item_options = {f"{it.skill} — {it.resource}": it.id for it in items}
            preselect = None
            if task and task.learning_item_id:
                for label, iid in item_options.items():
                    if iid == task.learning_item_id:
                        preselect = label
                        break

            with st.form("session_form"):
                selected_item = st.selectbox("Learning item", list(item_options.keys()),
                    index=list(item_options.keys()).index(preselect) if preselect else 0)
                duration = st.number_input("Duration (minutes)", min_value=1,
                    value=task.estimated_min or 30, step=5)
                takeaway = st.text_area("What did you learn?", placeholder="Core insight, breakthrough, or takeaway (Required)")
                confidence = st.slider("Confidence (1-5)", 1, 5, 3)

                col_save, col_skip = st.columns(2)
                with col_save:
                    save = st.form_submit_button("Save Session", type="primary", use_container_width=True)
                with col_skip:
                    skip = st.form_submit_button("Skip", use_container_width=True)

                if save:
                    if takeaway.strip():
                        from services import learning
                        with get_conn() as conn:
                            learning.log_session(
                                item_id=item_options[selected_item],
                                session_date=today_iso,
                                duration_min=duration,
                                takeaway=takeaway.strip(),
                                confidence=confidence,
                                task_id=session_task_id,
                                conn=conn,
                            )
                        del st.session_state[key]
                        st.rerun()
                    else:
                        st.error("Takeaway is required!")
                if skip:
                    del st.session_state[key]
                    st.rerun()

        session_dialog()
        break
