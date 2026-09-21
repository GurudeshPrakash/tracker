"""Settings page — backup, export, restore, recurring tasks, reminders.

Layout per spec Section 8.8.
"""

import os
import streamlit as st

st.set_page_config(page_title="Settings | Tracker", page_icon="⚙️", layout="wide")

from lib.dates import today
from db.connection import get_conn
from db import repository as repo
from db.models import RECURRING_RULES, PRIORITIES, CATEGORIES
from services import backup
from services import recurring as rec_svc

today_iso = today()
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

st.title("⚙️ Settings")

tab1, tab2, tab3, tab4 = st.tabs(["Backups", "Recurring Tasks", "Export/Import", "Reminders"])

# ---------------------------------------------------------------------------
# Tab 1: Backups
# ---------------------------------------------------------------------------
with tab1:
    st.subheader("💾 Backups")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("📦 Backup Now", use_container_width=True, type="primary"):
            try:
                path = backup.backup_now()
                st.success(f"✅ Backup created: {os.path.basename(path)}")
            except FileNotFoundError:
                st.error("No database found to back up.")

    st.markdown("---")
    st.subheader("📂 Available Backups")

    backups = backup.list_backups()
    if backups:
        for b in backups:
            cols = st.columns([3, 1, 1])
            with cols[0]:
                st.markdown(f"**{b['name']}**")
            with cols[1]:
                st.caption(f"{b['size_mb']} MB")
            with cols[2]:
                st.caption(b['created'])
    else:
        st.info("No backups yet. Backups are created automatically each day.")

    st.markdown("---")
    st.subheader("🔄 Restore from Backup")
    st.warning("⚠️ Restoring will replace your current database. A pre-restore backup is created automatically.")

    uploaded = st.file_uploader("Upload a .db backup file", type=["db"])
    confirm = st.checkbox("I understand this will replace my current data")

    if uploaded and confirm:
        if st.button("Restore", type="primary"):
            try:
                backup.restore_from(uploaded.read())
                st.success("✅ Database restored successfully! Please refresh the app.")
            except ValueError as e:
                st.error(f"❌ {e}")

    # Or restore from existing backup
    if backups:
        st.markdown("**Or restore from an existing backup:**")
        backup_names = [b['name'] for b in backups]
        selected_backup = st.selectbox("Select backup", backup_names)
        if selected_backup and confirm:
            if st.button("Restore Selected", key="restore_existing"):
                selected_b = next(b for b in backups if b['name'] == selected_backup)
                try:
                    backup.restore_from(selected_b['path'])
                    st.success("✅ Database restored! Please refresh the app.")
                except ValueError as e:
                    st.error(f"❌ {e}")

# ---------------------------------------------------------------------------
# Tab 2: Recurring Tasks
# ---------------------------------------------------------------------------
with tab2:
    st.subheader("🔁 Recurring Tasks")

    with get_conn() as conn:
        rec_tasks = repo.get_all_recurring_tasks(conn)

    if rec_tasks:
        for rt in rec_tasks:
            cols = st.columns([3, 1, 1, 1, 0.5])
            with cols[0]:
                status_icon = "🟢" if rt.active else "⏸️"
                st.markdown(f"{status_icon} **{rt.title}**")
            with cols[1]:
                st.caption(rt.rule)
            with cols[2]:
                st.caption(f"{rt.priority} / {rt.category}")
            with cols[3]:
                if rt.weekday is not None:
                    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
                    st.caption(days[rt.weekday])
                elif rt.day_of_month is not None:
                    st.caption(f"Day {rt.day_of_month}")
            with cols[4]:
                if rt.active:
                    if st.button("⏸️", key=f"pause_rec_{rt.id}"):
                        with get_conn() as conn:
                            repo.update_recurring_task(conn, rt.id, active=0)
                        st.rerun()
                else:
                    if st.button("▶️", key=f"resume_rec_{rt.id}"):
                        with get_conn() as conn:
                            repo.update_recurring_task(conn, rt.id, active=1)
                        st.rerun()
    else:
        st.info("No recurring tasks configured yet.")

    st.markdown("---")
    st.subheader("➕ Add Recurring Task")

    with st.form("add_recurring_form", clear_on_submit=True):
        r_cols = st.columns([2, 1, 1, 1])
        with r_cols[0]:
            r_title = st.text_input("Title", placeholder="e.g. Review flashcards")
        with r_cols[1]:
            r_rule = st.selectbox("Rule", RECURRING_RULES)
        with r_cols[2]:
            r_priority = st.selectbox("Priority", PRIORITIES, index=1)
        with r_cols[3]:
            r_category = st.selectbox("Category", CATEGORIES)

        r_cols2 = st.columns(4)
        with r_cols2[0]:
            r_weekday = st.selectbox("Weekday (for weekly)", [None, 0, 1, 2, 3, 4, 5, 6],
                format_func=lambda x: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][x] if x is not None else "—")
        with r_cols2[1]:
            r_day = st.number_input("Day of month (for monthly)", min_value=0, max_value=31, value=0)
        with r_cols2[2]:
            from datetime import date as dt_date
            r_start = st.date_input("Start date", value=dt_date.fromisoformat(today_iso))
        with r_cols2[3]:
            r_estimate = st.number_input("Est. minutes", min_value=0, value=0, step=5)

        if st.form_submit_button("Create Recurring Task", use_container_width=True):
            if r_title.strip():
                with get_conn() as conn:
                    repo.create_recurring_task(
                        conn,
                        title=r_title.strip(),
                        rule=r_rule,
                        start_date=r_start.isoformat(),
                        priority=r_priority,
                        category=r_category,
                        weekday=r_weekday,
                        day_of_month=r_day if r_day > 0 else None,
                        estimated_min=r_estimate if r_estimate > 0 else None,
                    )
                st.rerun()
            else:
                st.error("Title is required.")

# ---------------------------------------------------------------------------
# Tab 3: Export/Import
# ---------------------------------------------------------------------------
with tab3:
    st.subheader("📤 Export All Data as CSV")
    st.markdown("Download a ZIP file containing one CSV per database table.")

    if st.button("📥 Generate CSV Export", use_container_width=True, type="primary"):
        try:
            zip_bytes = backup.export_csv_zip()
            st.download_button(
                label="⬇️ Download ZIP",
                data=zip_bytes,
                file_name="tracker_export.zip",
                mime="application/zip",
            )
        except Exception as e:
            st.error(f"Export failed: {e}")

# ---------------------------------------------------------------------------
# Tab 4: Reminders (Section 10)
# ---------------------------------------------------------------------------
with tab4:
    st.subheader("⏰ Desktop Reminders")
    st.markdown(
        "Use Windows Task Scheduler to get morning and evening notifications. "
        "Copy and paste the commands below into an **elevated** PowerShell."
    )

    venv_python = os.path.join(_PROJECT_ROOT, ".venv", "Scripts", "pythonw.exe")
    notify_script = os.path.join(_PROJECT_ROOT, "reminders", "notify.py")

    morning_cmd = (
        f'schtasks /Create /SC DAILY /ST 08:30 /TN "TrackerMorning" '
        f'/TR "\\"{venv_python}\\" \\"{notify_script}\\" morning"'
    )
    evening_cmd = (
        f'schtasks /Create /SC DAILY /ST 20:30 /TN "TrackerEvening" '
        f'/TR "\\"{venv_python}\\" \\"{notify_script}\\" evening"'
    )

    st.code(morning_cmd, language="bat")
    st.code(evening_cmd, language="bat")

    st.markdown("---")
    st.markdown("**To remove reminders:**")
    st.code('schtasks /Delete /TN "TrackerMorning" /F', language="bat")
    st.code('schtasks /Delete /TN "TrackerEvening" /F', language="bat")
