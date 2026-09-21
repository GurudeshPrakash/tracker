"""Desktop notification script for Windows Task Scheduler.

Usage: python notify.py morning|evening

Does NOT import Streamlit. Fails silently with logging.
See spec Section 10.
"""

import os
import sys
import logging
from datetime import datetime

# Setup logging to data/notify.log
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_LOG_FILE = os.path.join(_PROJECT_ROOT, "data", "notify.log")

os.makedirs(os.path.dirname(_LOG_FILE), exist_ok=True)
logging.basicConfig(
    filename=_LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

# Add project root to path
sys.path.insert(0, _PROJECT_ROOT)


def _get_morning_message() -> tuple[str, str]:
    """Return (title, message) for the morning notification."""
    try:
        from db.connection import get_conn
        from db import repository as repo
        from lib.dates import today

        today_iso = today()
        with get_conn() as conn:
            todo_tasks = repo.get_todo_tasks_for_date(conn, today_iso)
            overdue = repo.get_overdue_tasks(conn, today_iso)

        total = len(todo_tasks) + len(overdue)
        return (
            "☀️ Plan Your Day",
            f"You have {total} task{'s' if total != 1 else ''} waiting. Open Tracker to get started.",
        )
    except Exception as e:
        logging.error(f"Morning notification error: {e}")
        return ("☀️ Plan Your Day", "Open Tracker to plan your day.")


def _get_evening_message() -> tuple[str, str] | None:
    """Return (title, message) for evening, or None if day already closed."""
    try:
        from db.connection import get_conn
        from db import repository as repo
        from lib.dates import today

        today_iso = today()
        with get_conn() as conn:
            existing = repo.get_daily_update(conn, today_iso)

        if existing:
            # Day already closed — skip notification
            return None

        return (
            "🌙 Close Your Day",
            "Close your day. Takes 2 minutes.",
        )
    except Exception as e:
        logging.error(f"Evening notification error: {e}")
        return ("🌙 Close Your Day", "Don't forget to close your day in Tracker.")


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ("morning", "evening"):
        print("Usage: python notify.py morning|evening")
        sys.exit(1)

    mode = sys.argv[1]

    try:
        from plyer import notification

        if mode == "morning":
            title, message = _get_morning_message()
            notification.notify(title=title, message=message, timeout=10)
            logging.info(f"Morning notification sent: {message}")

        elif mode == "evening":
            result = _get_evening_message()
            if result is None:
                logging.info("Evening notification skipped: day already closed.")
                return
            title, message = result
            notification.notify(title=title, message=message, timeout=10)
            logging.info(f"Evening notification sent: {message}")

    except Exception as e:
        logging.error(f"Notification error ({mode}): {e}")
        # Fail silently as specified


if __name__ == "__main__":
    main()
