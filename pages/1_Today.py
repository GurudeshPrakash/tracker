"""Today page — daily task management.

Layout per spec Section 8.2: header, suggestions, quick add,
top-3, other tasks by priority, completed, overdue, close day button.
"""

import streamlit as st

st.set_page_config(page_title="Today | Tracker", page_icon="📋", layout="wide")

from lib.dates import today
from lib.ui import priority_badge, category_badge, rollover_badge, format_minutes
from db.connection import get_conn
from db import repository as repo
from services import tasks as task_svc
from services import suggestions as suggest_svc

today_iso = today()

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.title(f"📋 Today — {today_iso}")

with get_conn() as conn:
    done_count = repo.count_completed_for_date(conn, today_iso)
    todo_tasks = repo.get_todo_tasks_for_date(conn, today_iso)
    planned_count = len(todo_tasks) + done_count

st.markdown(f"**Progress:** {done_count} / {planned_count} tasks done")
if planned_count > 0:
    st.progress(done_count / planned_count)

# ---------------------------------------------------------------------------
# Suggested Tasks (Section 7.7)
# ---------------------------------------------------------------------------
with get_conn() as conn:
    suggestions = suggest_svc.suggest_tasks_for(today_iso, conn)

if suggestions:
    st.subheader("💡 Suggested Tasks")
    for sug in suggestions:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"**{sug.title}**")
            st.caption(sug.reason)
        with col2:
            if st.button("Add to today", key=f"add_sug_{sug.goal_id}"):
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
    st.markdown("---")

# ---------------------------------------------------------------------------
# Quick Add (Section 8.2)
# ---------------------------------------------------------------------------
with st.form("quick_add", clear_on_submit=True):
    st.subheader("➕ Quick Add Task")
    qa_cols = st.columns([3, 1, 1, 1])
    with qa_cols[0]:
        new_title = st.text_input("Task", placeholder="What needs doing?", label_visibility="collapsed")
    with qa_cols[1]:
        new_priority = st.selectbox("Priority", ["medium", "high", "low"], label_visibility="collapsed")
    with qa_cols[2]:
        new_category = st.selectbox("Category", ["work", "learning", "personal"], label_visibility="collapsed")
    with qa_cols[3]:
        new_estimate = st.number_input("Est. min", min_value=0, value=0, step=5, label_visibility="collapsed")

    submitted = st.form_submit_button("Add Task", use_container_width=True)
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

st.markdown("---")


# ---------------------------------------------------------------------------
# Helpers for rendering task rows
# ---------------------------------------------------------------------------
def _render_task_row(task, conn_getter):
    """Render a single task row with checkbox, badges, and actions."""
    cols = st.columns([0.5, 3, 1, 1, 1, 0.5, 0.5, 0.5])

    with cols[0]:
        done = st.checkbox("✓", value=False, key=f"done_{task.id}", label_visibility="collapsed")
        if done:
            with conn_getter() as conn:
                try:
                    task_svc.complete(task.id, conn, today_iso)
                    # If learning task, show session dialog
                    if task.category == "learning":
                        st.session_state[f"log_session_{task.id}"] = True
                except ValueError as e:
                    st.error(str(e))
            st.rerun()

    with cols[1]:
        title_text = task.title
        if task.notes:
            title_text += f" *(📝)*"
        st.markdown(title_text)

        # Rollover warning
        if task.rollover_count >= 3:
            st.caption(rollover_badge(task.rollover_count))

        # Subtasks
        with conn_getter() as conn:
            subtasks = repo.get_subtasks(conn, task.id)
        if subtasks:
            for sub in subtasks:
                status_icon = "✅" if sub.status == "done" else "⬜"
                st.caption(f"  {status_icon} {sub.title}")

    with cols[2]:
        st.caption(f"{priority_badge(task.priority)} {task.priority}")

    with cols[3]:
        st.caption(f"{category_badge(task.category)} {task.category}")

    with cols[4]:
        if task.estimated_min:
            st.caption(f"⏱️ {format_minutes(task.estimated_min)}")

    with cols[5]:
        # Top-3 toggle
        is_top3 = bool(task.is_top3)
        star = "⭐" if is_top3 else "☆"
        if st.button(star, key=f"star_{task.id}"):
            with conn_getter() as conn:
                try:
                    task_svc.set_top3(task.id, not is_top3, conn)
                except ValueError as e:
                    st.error(str(e))
            st.rerun()

    with cols[6]:
        if st.button("✏️", key=f"edit_{task.id}"):
            st.session_state["editing_task"] = task.id

    with cols[7]:
        if st.button("🗑️", key=f"drop_{task.id}"):
            with conn_getter() as conn:
                task_svc.drop(task.id, conn)
            st.rerun()

    # Rollover warning actions (Section 7.3)
    if task.rollover_count >= 3:
        rc = st.columns(3)
        with rc[0]:
            if st.button("Break down", key=f"break_{task.id}"):
                st.session_state["adding_subtask_to"] = task.id
        with rc[1]:
            if st.button("Reschedule", key=f"resched_{task.id}"):
                st.session_state["rescheduling_task"] = task.id
        with rc[2]:
            if st.button("Drop", key=f"rdrop_{task.id}"):
                with conn_getter() as conn:
                    task_svc.drop(task.id, conn)
                st.rerun()


# ---------------------------------------------------------------------------
# Top 3 Priorities
# ---------------------------------------------------------------------------
st.subheader("🌟 Top 3 Priorities")

with get_conn() as conn:
    top3 = repo.get_top3_tasks(conn, today_iso)

if top3:
    for task in top3:
        _render_task_row(task, get_conn)
else:
    st.info("No top-3 priorities set. Star tasks to mark them as priorities.")

st.markdown("---")

# ---------------------------------------------------------------------------
# Other Tasks by Priority
# ---------------------------------------------------------------------------
with get_conn() as conn:
    all_todo = repo.get_todo_tasks_for_date(conn, today_iso)

other_tasks = [t for t in all_todo if not t.is_top3 and t.parent_task_id is None]

for priority_label, priority_key in [("🔴 High", "high"), ("🟡 Medium", "medium"), ("🟢 Low", "low")]:
    tasks_in_group = [t for t in other_tasks if t.priority == priority_key]
    if tasks_in_group:
        st.subheader(priority_label)
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
            cols = st.columns([0.5, 3, 1, 1])
            with cols[0]:
                undone = st.checkbox("✓", value=True, key=f"undone_{task.id}", label_visibility="collapsed")
                if not undone:
                    with get_conn() as conn:
                        task_svc.uncomplete(task.id, conn)
                    st.rerun()
            with cols[1]:
                st.markdown(f"~~{task.title}~~")
            with cols[2]:
                st.caption(f"{category_badge(task.category)} {task.category}")
            with cols[3]:
                if task.actual_min:
                    st.caption(f"⏱️ {format_minutes(task.actual_min)}")

# ---------------------------------------------------------------------------
# Overdue Tasks
# ---------------------------------------------------------------------------
with get_conn() as conn:
    overdue = repo.get_overdue_tasks(conn, today_iso)

if overdue:
    with st.expander(f"⚠️ Overdue ({len(overdue)})", expanded=True):
        for task in overdue:
            st.warning(f"**{task.title}** — Due: {task.due_date} {priority_badge(task.priority)}")

st.markdown("---")

# ---------------------------------------------------------------------------
# Close Day Button
# ---------------------------------------------------------------------------
if st.button("🌙 Close My Day", use_container_width=True, type="primary"):
    st.switch_page("pages/2_Daily_Update.py")

# ---------------------------------------------------------------------------
# Edit Task Dialog
# ---------------------------------------------------------------------------
if "editing_task" in st.session_state:
    task_id = st.session_state["editing_task"]

    @st.dialog("Edit Task")
    def edit_dialog():
        with get_conn() as conn:
            task = repo.get_task(conn, task_id)
        if not task:
            st.error("Task not found")
            return

        with st.form("edit_form"):
            title = st.text_input("Title", value=task.title)
            notes = st.text_area("Notes", value=task.notes or "")
            priority = st.selectbox("Priority", ["high", "medium", "low"],
                                     index=["high", "medium", "low"].index(task.priority))
            category = st.selectbox("Category", ["work", "learning", "personal"],
                                     index=["work", "learning", "personal"].index(task.category))
            due_date = st.date_input("Due date", value=None)
            estimated = st.number_input("Estimated minutes", min_value=0,
                                         value=task.estimated_min or 0, step=5)

            if st.form_submit_button("Save"):
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

    @st.dialog("Break Down Task")
    def subtask_dialog():
        with get_conn() as conn:
            parent = repo.get_task(conn, parent_id)
        if not parent:
            st.error("Parent task not found")
            return

        st.markdown(f"Breaking down: **{parent.title}**")

        with st.form("subtask_form"):
            sub_title = st.text_input("Subtask title")
            if st.form_submit_button("Add Subtask"):
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

    @st.dialog("Reschedule Task")
    def reschedule_dialog():
        with get_conn() as conn:
            task = repo.get_task(conn, resched_id)
        if not task:
            st.error("Task not found")
            return

        st.markdown(f"Rescheduling: **{task.title}**")
        new_date = st.date_input("New date")

        if st.button("Reschedule"):
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
                takeaway = st.text_area("What did you learn?", placeholder="Required")
                confidence = st.slider("Confidence (1-5)", 1, 5, 3)

                col_save, col_skip = st.columns(2)
                with col_save:
                    save = st.form_submit_button("Save Session")
                with col_skip:
                    skip = st.form_submit_button("Skip")

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
        break  # Only show one dialog at a time
