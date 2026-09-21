# Daily Work & Self-Learning Tracker: Implementation Specification

**Target:** Windows PC, single user, fully local
**Stack:** Python 3.11+, Streamlit, SQLite (`sqlite3`), pandas, Plotly, pytest
**Audience:** a coding agent (Google Antigravity) plus the developer supervising it

---

## 0. How to use this document with Antigravity

1. Create an empty project folder and open it as the workspace.
2. Put this file in the folder as `SPEC.md`. Put **Section 3 (Agent Rules)** wherever your agent setup reads persistent instructions (workspace rules or a project instructions file). If unsure, keep it in `SPEC.md` and start every task with "Read SPEC.md sections 3, 6 and 7 first."
3. Build **one phase at a time** (Section 13). Each phase has a ready-to-paste prompt, a checklist, and acceptance criteria.
4. After each phase: run `pytest`, launch the app, click through the acceptance criteria by hand, then commit to Git before starting the next phase.
5. Do not ask the agent to build everything in one go. Small phases produce reviewable diffs and fewer hidden bugs.

---

## 1. Product overview

### 1.1 Purpose
A personal system that runs a daily loop:

**Morning: plan the day → During the day: tick off tasks → Evening: close the day with a progress update → Unfinished work rolls to tomorrow → Goals suggest what to study next.**

It also records self-learning (what was studied, for how long, what was learned, how confident) so progress over weeks and months is visible.

### 1.2 Core features (MVP = Phases 0-2)
- To-do list with priority, category, due date, top-3 daily priorities
- Daily update (evening close-out) with automatic rollover of unfinished tasks
- Learning tracker: skills/resources, study sessions, takeaways, confidence

### 1.3 Later features (Phases 3-6)
- Goals with progress and rule-based suggestions
- Insights (charts, streaks) and weekly review
- Recurring tasks, backups, CSV export, desktop reminders

### 1.4 Non-goals
- No accounts, login, cloud sync or multi-user support
- No AI or LLM features (suggestions are simple rules)
- No mobile app

### 1.5 Design principle
**Logging must take under 30 seconds.** If a form has more than 5 required fields, simplify it. Every feature must reduce or reuse typing (for example, completed tasks pre-fill the daily update).

---

## 2. Tech stack and decisions

| Concern | Decision | Reason |
|---|---|---|
| Language | Python 3.11+ | Developer preference |
| UI | Streamlit (>= 1.40) | Forms, tabs, charts in pure Python; opens in browser at localhost |
| Database | SQLite via the standard `sqlite3` module | Zero setup, single file, easy to back up |
| Models | `dataclasses` (no ORM) | Fewer moving parts and easier for an agent to get right than an ORM |
| Data/stats | pandas | Weekly totals, trends |
| Charts | Plotly (`plotly.express`) | Interactive charts, good Streamlit support |
| Notifications | `plyer` + Windows Task Scheduler | Real desktop pop-ups even when the app is closed |
| Tests | pytest | Rollover, streak and suggestion logic must be tested |
| Launch | `run.bat` | Double-click start |

**Decision:** raw `sqlite3` with a repository layer instead of SQLModel. This replaces the SQLModel mention in earlier planning notes; remove `sqlmodel` from the install command.

---

## 3. Agent Rules (persistent instructions)

Copy this section into your agent's rules/instructions.

1. **Layering is strict.** `pages/*.py` and `app.py` contain only UI code. All logic goes in `services/`. All SQL goes in `db/repository.py`. UI code never writes SQL; services never import Streamlit.
2. **Dates are local ISO strings** (`YYYY-MM-DD`), stored as `TEXT`. Never store UTC timestamps for calendar dates. Get today's date only from `lib/dates.py::today()` so tests can override it.
3. **Every service function that depends on "today" takes it as a parameter** (with a default of `today()`), so it can be tested with fixed dates.
4. **Use a fresh SQLite connection per operation** via a context manager (`with get_conn() as conn:`). Enable `PRAGMA foreign_keys = ON` on every connection. Use parameterised queries only; never format values into SQL strings.
5. **Type hints and docstrings** on all public functions. Keep functions short and single-purpose.
6. **Do not put business logic in Streamlit callbacks.** Callbacks call a service function, then trigger `st.rerun()` if needed.
7. **Schema changes go through migrations** (Section 6.4). Never edit an applied migration; add a new one.
8. **Every service in `services/` has tests** in `tests/`. Tests use a temporary database (pytest `tmp_path` fixture), never `data/tracker.db`.
9. **No new dependencies** beyond `requirements.txt` without asking.
10. **Never delete user data silently.** Deleting a task is a soft action (`status = 'dropped'`) unless the user chooses "Delete permanently".
11. After each phase, update `README.md` with what works and how to run it.

---

## 4. Project structure

```
tracker/
├── app.py                      # Streamlit entry point: startup tasks + home dashboard
├── pages/
│   ├── 1_Today.py
│   ├── 2_Daily_Update.py
│   ├── 3_Learning.py
│   ├── 4_Goals.py
│   ├── 5_Insights.py
│   ├── 6_Weekly_Review.py
│   └── 7_Settings.py           # backup, export, import
├── db/
│   ├── __init__.py
│   ├── connection.py           # get_conn(), DB path, run_migrations()
│   ├── migrations.py           # MIGRATIONS dict {version: sql}
│   ├── models.py               # dataclasses: Task, DailyUpdate, ...
│   └── repository.py           # all SQL functions
├── services/
│   ├── __init__.py
│   ├── tasks.py                # create/complete/drop/top-3 rules
│   ├── rollover.py             # carry unfinished tasks forward
│   ├── daily_update.py         # build prefill, close day
│   ├── learning.py             # sessions, totals per skill
│   ├── goals.py                # progress + pace
│   ├── suggestions.py          # behind-schedule rules
│   ├── recurring.py            # generate recurring task instances
│   ├── stats.py                # streaks, completion rate, weekly totals
│   └── backup.py               # auto backup, CSV export, restore
├── lib/
│   ├── dates.py                # today(), week_start(), date_range()
│   └── ui.py                   # shared Streamlit helpers (badges, formatters)
├── reminders/
│   └── notify.py               # run by Windows Task Scheduler
├── tests/
│   ├── conftest.py             # temp-db fixture
│   ├── test_rollover.py
│   ├── test_tasks.py
│   ├── test_daily_update.py
│   ├── test_stats.py
│   ├── test_suggestions.py
│   ├── test_recurring.py
│   └── test_backup.py
├── data/                       # tracker.db lives here (git-ignored)
├── backups/                    # dated DB copies (git-ignored)
├── requirements.txt
├── run.bat
├── .gitignore
├── README.md
└── SPEC.md                     # this file
```

---

## 5. Setup

### 5.1 `requirements.txt`
```
streamlit>=1.40
pandas>=2.2
plotly>=5.24
plyer>=2.1
pytest>=8.0
```

### 5.2 First-time setup (PowerShell)
```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
git init
streamlit run app.py
```

### 5.3 `run.bat`
```bat
@echo off
cd /d %~dp0
call .venv\Scripts\activate
streamlit run app.py
```

### 5.4 `.gitignore`
```
.venv/
__pycache__/
data/
backups/
*.db
.pytest_cache/
```

---

## 6. Database

### 6.1 Conventions
- Dates: `TEXT` in `YYYY-MM-DD`. Timestamps: `TEXT` from `datetime('now','localtime')`.
- Booleans: `INTEGER` 0/1.
- Enumerated values enforced with `CHECK` constraints.
- Foreign keys always on.

### 6.2 Schema (migration version 1)

```sql
CREATE TABLE schema_version (
    version INTEGER NOT NULL
);
INSERT INTO schema_version (version) VALUES (1);

CREATE TABLE goal (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    title         TEXT NOT NULL,
    target_type   TEXT NOT NULL CHECK (target_type IN ('weekly_hours','total_hours')),
    target_hours  REAL NOT NULL CHECK (target_hours > 0),
    start_date    TEXT NOT NULL,
    target_date   TEXT,                       -- required for total_hours goals (enforced in service)
    status        TEXT NOT NULL DEFAULT 'active'
                  CHECK (status IN ('active','done','paused','dropped')),
    created_at    TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);

CREATE TABLE learning_item (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    skill         TEXT NOT NULL,              -- e.g. "SQL"
    resource      TEXT NOT NULL,              -- e.g. "Mode SQL tutorial"
    resource_type TEXT NOT NULL DEFAULT 'course'
                  CHECK (resource_type IN ('course','book','video','article','practice','project','other')),
    status        TEXT NOT NULL DEFAULT 'in_progress'
                  CHECK (status IN ('planned','in_progress','done','paused')),
    goal_id       INTEGER REFERENCES goal(id) ON DELETE SET NULL,
    created_at    TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);

CREATE TABLE recurring_task (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    title            TEXT NOT NULL,
    priority         TEXT NOT NULL DEFAULT 'medium' CHECK (priority IN ('high','medium','low')),
    category         TEXT NOT NULL DEFAULT 'work'   CHECK (category IN ('work','learning','personal')),
    goal_id          INTEGER REFERENCES goal(id) ON DELETE SET NULL,
    learning_item_id INTEGER REFERENCES learning_item(id) ON DELETE SET NULL,
    estimated_min    INTEGER,
    rule             TEXT NOT NULL CHECK (rule IN ('daily','weekdays','weekly','monthly')),
    weekday          INTEGER CHECK (weekday BETWEEN 0 AND 6),   -- 0 = Monday, used by 'weekly'
    day_of_month     INTEGER CHECK (day_of_month BETWEEN 1 AND 31),
    start_date       TEXT NOT NULL,
    end_date         TEXT,
    active           INTEGER NOT NULL DEFAULT 1,
    last_generated   TEXT
);

CREATE TABLE task (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    title            TEXT NOT NULL,
    notes            TEXT,
    planned_date     TEXT,                    -- the day I intend to do it; NULL = backlog
    due_date         TEXT,                    -- hard deadline (optional)
    priority         TEXT NOT NULL DEFAULT 'medium' CHECK (priority IN ('high','medium','low')),
    category         TEXT NOT NULL DEFAULT 'work'   CHECK (category IN ('work','learning','personal')),
    goal_id          INTEGER REFERENCES goal(id) ON DELETE SET NULL,
    learning_item_id INTEGER REFERENCES learning_item(id) ON DELETE SET NULL,
    parent_task_id   INTEGER REFERENCES task(id) ON DELETE CASCADE,   -- subtasks
    recurring_id     INTEGER REFERENCES recurring_task(id) ON DELETE SET NULL,
    status           TEXT NOT NULL DEFAULT 'todo' CHECK (status IN ('todo','done','dropped')),
    is_top3          INTEGER NOT NULL DEFAULT 0,
    rollover_count   INTEGER NOT NULL DEFAULT 0,
    estimated_min    INTEGER,
    actual_min       INTEGER,
    completed_at     TEXT,                    -- local timestamp
    completed_date   TEXT,                    -- local date, used for reporting
    created_at       TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);
CREATE INDEX idx_task_planned ON task(planned_date, status);
CREATE INDEX idx_task_completed_date ON task(completed_date);
CREATE UNIQUE INDEX idx_task_recurring_day
    ON task(recurring_id, planned_date) WHERE recurring_id IS NOT NULL;

CREATE TABLE learning_session (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    learning_item_id INTEGER NOT NULL REFERENCES learning_item(id) ON DELETE CASCADE,
    task_id          INTEGER REFERENCES task(id) ON DELETE SET NULL,
    session_date     TEXT NOT NULL,
    duration_min     INTEGER NOT NULL CHECK (duration_min > 0),
    takeaway         TEXT NOT NULL,           -- "what I learned", required on purpose
    confidence       INTEGER CHECK (confidence BETWEEN 1 AND 5),
    created_at       TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);
CREATE INDEX idx_session_date ON learning_session(session_date);

CREATE TABLE daily_update (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    date              TEXT NOT NULL UNIQUE,
    planned_count     INTEGER NOT NULL DEFAULT 0,   -- snapshot taken when the day is closed
    completed_count   INTEGER NOT NULL DEFAULT 0,   -- snapshot taken when the day is closed
    completed_summary TEXT,
    learned_today     TEXT,
    study_minutes     INTEGER NOT NULL DEFAULT 0,
    day_rating        INTEGER CHECK (day_rating BETWEEN 1 AND 5),
    blockers          TEXT,
    tomorrow_focus    TEXT,
    created_at        TEXT NOT NULL DEFAULT (datetime('now','localtime')),
    updated_at        TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);

CREATE TABLE review (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    week_start  TEXT NOT NULL UNIQUE,           -- Monday of the week
    wins        TEXT,
    blockers    TEXT,
    next_focus  TEXT,
    created_at  TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);
```

**Why `planned_count` and `completed_count` are stored on `daily_update`:** rollover changes a task's `planned_date`, so the historical "how many did I plan that day" can no longer be recomputed from the task table. Snapshotting both numbers at close time makes the completion-rate trend accurate.

### 6.3 Enumerations (define once in `db/models.py`)
```python
PRIORITIES = ("high", "medium", "low")
CATEGORIES = ("work", "learning", "personal")
TASK_STATUSES = ("todo", "done", "dropped")
RESOURCE_TYPES = ("course", "book", "video", "article", "practice", "project", "other")
```

### 6.4 Migration mechanism
`db/migrations.py`:
```python
MIGRATIONS: dict[int, str] = {
    1: SCHEMA_V1_SQL,      # the SQL in 6.2
    # 2: "ALTER TABLE task ADD COLUMN ...;",
}
```
`run_migrations(conn)`:
1. If `schema_version` table does not exist, current version = 0.
2. For each version greater than current, in ascending order, `executescript` the SQL, then update `schema_version`, inside a transaction.
3. Called from `startup()` (Section 9.1) and from test fixtures.

---

## 7. Domain rules (the important logic)

### 7.1 Dates (`lib/dates.py`)
```python
def today() -> str                      # local date as 'YYYY-MM-DD'
def add_days(iso: str, n: int) -> str
def week_start(iso: str) -> str         # Monday of that week
def week_end(iso: str) -> str           # Sunday
def date_range(start: str, end: str) -> list[str]   # inclusive
def weekday(iso: str) -> int            # 0 = Monday
```

### 7.2 Task lifecycle
- New task: `status='todo'`, `planned_date` defaults to today (or NULL if added from the Backlog view).
- **Complete:** set `status='done'`, `completed_at=now`, `completed_date=today`, `is_top3` stays as is (for history). If `category == 'learning'`, the UI offers to log a study session (Section 8.4).
- **Un-complete:** back to `todo`, clear `completed_at` and `completed_date`.
- **Drop:** `status='dropped'`, removed from all active views; can be restored.
- **Subtasks:** a task with `parent_task_id` shows nested under its parent. A parent cannot be marked done while subtasks are `todo` (service raises `ValueError`; UI shows a message).
- **Top 3:** at most **3** tasks with `is_top3=1` and `status='todo'` per `planned_date`. Setting a fourth raises `ValueError("Only 3 priorities per day")`. When a task rolls over, `is_top3` is **kept** (it is still a priority).

### 7.3 Rollover (`services/rollover.py`) - must be idempotent
```python
def rollover(from_date: str, to_date: str, conn) -> int:
    """Move every todo task with planned_date <= from_date to to_date.
    Increment rollover_count by 1. Return number of tasks moved.
    Does not touch tasks with planned_date IS NULL (backlog), done, or dropped tasks."""
```
Two call sites:
1. **Close day** (evening): `rollover(today, tomorrow)`.
2. **App startup safety net:** `rollover(yesterday, today)`. This catches days where the daily update was never done. It moves tasks whose `planned_date < today`.

**Why it is idempotent:** after a rollover, no `todo` task has `planned_date <= from_date`, so a second run finds nothing. It also cannot double-count: closing today moves tasks to tomorrow; tomorrow's startup rollover looks for `planned_date <= yesterday (= today's closed day)` and finds none.

**Rollover warning:** tasks with `rollover_count >= 3` are flagged in the UI with a warning badge and three action buttons: *Break down* (opens subtask form), *Reschedule* (date picker, resets nothing), *Drop*.

### 7.4 Daily update / closing the day (`services/daily_update.py`)
```python
def build_prefill(date: str, conn) -> dict:
    """Returns:
    completed_tasks: list[Task]      # completed_date == date
    open_tasks: list[Task]           # todo with planned_date == date
    study_minutes: int               # sum(duration_min) of sessions on date
    session_takeaways: list[str]     # takeaways logged on date
    existing: DailyUpdate | None
    """

def close_day(date: str, form: DailyUpdateForm, carry_task_ids: list[int], conn) -> DailyUpdate:
    """In a single transaction:
    1. planned_count = number of tasks that were planned for `date` (todo + done with completed_date == date)
    2. completed_count = tasks with completed_date == date
    3. Upsert daily_update for `date` (form values + snapshot counts)
    4. For open tasks NOT in carry_task_ids: set status='dropped'
    5. rollover(date, add_days(date, 1)) for the rest
    Returns the saved DailyUpdate."""
```
- The form pre-fills `completed_summary` with the titles of completed tasks (one per line) and `study_minutes` from sessions, both editable.
- Re-opening a closed day shows the saved values and allows editing text fields (no second rollover; guard by checking that no `todo` tasks with `planned_date <= date` remain).
- Default for every open task: **carry to tomorrow** (checked). Unchecking = drop.

### 7.5 Learning (`services/learning.py`)
```python
def log_session(item_id, session_date, duration_min, takeaway, confidence=None, task_id=None, conn=...) -> int
def totals_by_skill(start: str, end: str, conn) -> list[dict]   # skill, minutes, sessions, avg_confidence
def minutes_for_goal(goal_id: int, start: str, end: str, conn) -> int
def recent_takeaways(limit: int = 20, conn=...) -> list[dict]
```
- `takeaway` is required and must be non-empty after stripping. This is the core habit of the app.
- Logging a session may optionally link to a completed learning task (`task_id`) and set its `actual_min` if that was empty.

### 7.6 Goals (`services/goals.py`)
```python
def goal_progress(goal_id: int, today: str, conn) -> dict:
    """Returns:
    done_hours: float                # all-time hours from linked learning items' sessions
    week_hours: float                # this Mon-Sun week
    target_hours: float
    percent: float                   # total_hours: done/target; weekly_hours: week_hours/target
    expected_percent: float | None   # for total_hours: elapsed_days / total_days between start and target_date
    status: 'on_track' | 'behind' | 'ahead' | 'complete'
    """
```
Rules:
- **weekly_hours** goal: `behind` if, on day *k* of the week (Mon=1..Sun=7), `week_hours < target_hours * (k - 1) / 7`. `complete` when `week_hours >= target_hours`.
- **total_hours** goal: `expected_percent = elapsed / total` (clamped 0-100). `behind` if `percent < expected_percent - 10`; `ahead` if `percent > expected_percent + 10`; else `on_track`. `complete` at 100.

### 7.7 Suggestions (`services/suggestions.py`)
```python
def suggest_tasks_for(date: str, conn) -> list[Suggestion]
# Suggestion = dataclass(goal_id, title, minutes, reason)
```
For each **active** goal:
- **weekly_hours:** `remaining_h = max(0, target - week_hours)`, `days_left = number of days from date to Sunday inclusive`, `minutes = ceil(remaining_h * 60 / days_left)`.
- **total_hours:** `remaining_h = target - done_hours`, `days_left = days from date to target_date inclusive` (minimum 1), `minutes = ceil(remaining_h * 60 / days_left)`.
- Only suggest if the goal is `behind` **or** `minutes > 0` and no task linked to that goal is already planned for `date`.
- Cap `minutes` at 180 and round up to the nearest 5.
- Title: `"Study {skill or goal title} ({minutes} min)"`. Reason: `"Behind on '{goal}': {done}h of {target}h"`.
- Suggestions are shown on the Today page with an **Add to today** button. They are never auto-created.

### 7.8 Recurring tasks (`services/recurring.py`)
```python
def generate_for_date(date: str, conn) -> int
```
For each active `recurring_task` where `start_date <= date` and (`end_date` is null or `>= date`):
- `daily`: always; `weekdays`: Mon-Fri; `weekly`: `weekday(date) == weekday` field; `monthly`: `date.day == day_of_month` (if the month is shorter, use the last day of the month).
- Insert a task with `planned_date=date`, copying title/priority/category/goal/item/estimate, `recurring_id=id`. The unique index makes this idempotent; use `INSERT OR IGNORE`.
- Called at startup for today, and for tomorrow when the day is closed.
- If the app was not opened for several days, generate **only for today** (do not backfill).

### 7.9 Stats (`services/stats.py`)
```python
def update_streak(today: str, conn) -> int
```
Number of consecutive calendar days ending today (or yesterday if today has no update yet) that each have a `daily_update` row.
```python
def completion_rate_series(start: str, end: str, conn) -> DataFrame     # date, planned, completed, rate
def minutes_by_category(start: str, end: str, conn) -> DataFrame        # category, minutes (sum of actual_min of done tasks)
def study_minutes_by_skill(start: str, end: str, conn) -> DataFrame
def study_minutes_per_week(weeks: int, today: str, conn) -> DataFrame
def average_rating(start: str, end: str, conn) -> float | None
def week_summary(week_start: str, conn) -> dict
```
`week_summary` returns: tasks completed, completion rate, study hours, average day rating, best day (highest rating, ties broken by most tasks completed), top skill by minutes, list of blockers text from that week's daily updates, list of takeaways.

---

## 8. Page specifications

### 8.1 Startup and shared behaviour (`app.py`)
```python
@st.cache_resource
def startup(today_iso: str):
    run_migrations()
    backup.auto_backup(today_iso)
    recurring.generate_for_date(today_iso)
    rollover.rollover(add_days(today_iso, -1), today_iso)
    return True
```
- Every page begins with `startup(today())`. Passing the date as the cache key means startup logic re-runs automatically after midnight if the app stays open.
- `app.py` home page shows: date, streak, tasks done today vs planned, study minutes today, any goal that is `behind`, and a button "Go to Today".
- Sidebar navigation comes from the `pages/` folder.

### 8.2 Today (`pages/1_Today.py`)
Layout, top to bottom:
1. **Header:** date, greeting, progress bar `done / planned`.
2. **Suggested tasks** (from 7.7): each with reason and *Add to today*. Hidden when there are none.
3. **Quick add:** a single-line text input plus priority and category selectors, submitted with Enter (use `st.form(clear_on_submit=True)`). Estimated minutes optional.
4. **Top 3 priorities:** the tasks flagged `is_top3`, shown prominently with checkboxes.
5. **Other tasks for today:** grouped by priority (high, medium, low). Each row: checkbox, title, category badge, estimate, ⭐ toggle for top 3, edit and drop buttons. Show a warning badge when `rollover_count >= 3` with the three actions from 7.3.
6. **Completed today:** collapsed expander.
7. **Overdue backlog:** tasks with `due_date < today` and `status='todo'`, shown in a highlighted expander.
8. **Button: "Close my day"** navigates to the Daily Update page.

Behaviour:
- Ticking a checkbox calls `tasks.complete(id)` via callback. If the task's category is `learning`, open the "Log study session" dialog (`@st.dialog`) pre-filled with the task's linked item and estimated minutes; the user can skip.
- Subtasks are indented under their parent.
- Editing opens a dialog with all task fields.

### 8.3 Daily Update (`pages/2_Daily_Update.py`)
1. Date selector (default today; allow past days to catch up).
2. **Summary panel:** completed count, open count, study minutes (from `build_prefill`).
3. **Form** (`st.form`):
   - Completed summary (text area, pre-filled from completed task titles)
   - What I learned today (text area, pre-filled from session takeaways)
   - Study minutes (number input, pre-filled)
   - Day rating (1-5, `st.feedback("stars")` or `st.slider`)
   - Blockers (text area)
   - Tomorrow's focus (text input)
   - **Open tasks:** a checkbox list, all checked by default = "carry to tomorrow"
4. Submit button **"Close day and plan tomorrow"** calls `close_day(...)`, then shows a confirmation with tomorrow's task list and any suggestions.
5. If the day is already closed: show the saved update, allow text edits, and a note that rollover already happened.

### 8.4 Learning (`pages/3_Learning.py`)
Tabs:
- **Skills & resources:** table of learning items with status; add/edit form (skill, resource, type, status, optional goal).
- **Log session:** form with item selector, date (default today), duration (minutes), takeaway (required text area), confidence (1-5). Submit adds a session and shows a success message with total time for that skill this week.
- **History:** filterable list (by skill, date range) of sessions with takeaways, newest first, plus a search box over takeaway text.
- **Review takeaways:** shows 5 random takeaways older than 7 days as a light spaced-repetition prompt, each with a "Still remember this?" yes/no that updates nothing (display only in v1).

### 8.5 Goals (`pages/4_Goals.py`)
- List of goals as cards: title, progress bar, status badge (on track / behind / ahead / complete), hours done vs target, linked resources.
- Add/edit goal form (title, type, target hours, start date, target date when needed).
- Buttons: mark done, pause, drop.
- Under each *behind* goal, show the suggested task from 7.7 with an *Add to today* button.

### 8.6 Insights (`pages/5_Insights.py`)
Date range selector (last 7 / 30 / 90 days / custom). Charts:
1. **Completion rate per day** (line, from `daily_update` snapshots).
2. **Time by category** (bar; from `actual_min`).
3. **Study minutes by skill** (bar).
4. **Study minutes per week** (line or bar for the last 12 weeks).
5. **Day rating trend** (line).
6. **Metrics row:** update streak, average rating, total study hours, tasks completed.
Handle empty data with a friendly "No data yet" message, never an exception.

### 8.7 Weekly Review (`pages/6_Weekly_Review.py`)
- Week selector (default: current week).
- Auto-filled summary from `week_summary` (read-only cards).
- Form: **Wins**, **Blockers**, **Next week's focus**. Saves to `review` (upsert on `week_start`).
- Below: list of past reviews.

### 8.8 Settings (`pages/7_Settings.py`)
- **Backup now** button (creates a dated copy immediately) and a list of backups with sizes.
- **Export all data as CSV** (zip with one CSV per table, download button).
- **Restore from backup:** upload or select a `.db` file. Before overwriting, automatically back up the current DB as `pre_restore_<timestamp>.db`. Require a confirmation checkbox.
- **Recurring tasks:** list, add, pause, delete.
- **Reminder setup:** shows the exact `schtasks` commands (Section 10) with the correct project path filled in.

---

## 9. Streamlit implementation notes (common pitfalls)

- Streamlit reruns the whole script on every interaction. Keep state in `st.session_state`, never in module-level variables.
- Use `st.form` for multi-field input so the app does not rerun on every keystroke.
- Use `key=` on every widget inside loops (for example `key=f"done_{task.id}"`) to avoid duplicate widget errors.
- After writing to the DB from a callback, call `st.rerun()` so lists refresh.
- Do **not** cache DB reads with `st.cache_data` unless you clear the cache after every write. Simpler: do not cache.
- Dialogs: use `@st.dialog("Title")` (Streamlit >= 1.37).
- Wide layout: `st.set_page_config(page_title="Tracker", page_icon="✅", layout="wide")` as the first Streamlit call on each page.

---

## 10. Reminders (`reminders/notify.py`)

```python
# usage: python notify.py morning|evening
```
- `morning`: notification "Plan your day. You have N tasks waiting." (count of todo tasks planned for today or overdue).
- `evening`: **only notify if there is no `daily_update` for today**: "Close your day. Takes 2 minutes."
- Uses `plyer.notification.notify(title=..., message=..., timeout=10)`. Reads the DB directly through `db/repository.py`; does not import Streamlit.
- Exits silently on any error (log to `data/notify.log`).

**Windows Task Scheduler setup** (Settings page displays these with real paths):
```bat
schtasks /Create /SC DAILY /ST 08:30 /TN "TrackerMorning" /TR "\"C:\path\to\tracker\.venv\Scripts\pythonw.exe\" \"C:\path\to\tracker\reminders\notify.py\" morning"
schtasks /Create /SC DAILY /ST 20:30 /TN "TrackerEvening" /TR "\"C:\path\to\tracker\.venv\Scripts\pythonw.exe\" \"C:\path\to\tracker\reminders\notify.py\" evening"
```
`pythonw.exe` avoids a flashing console window. Remove later with `schtasks /Delete /TN "TrackerMorning" /F`.

---

## 11. Backup and export (`services/backup.py`)

```python
def auto_backup(today_iso: str, keep: int = 30) -> str | None
def backup_now() -> str
def list_backups() -> list[dict]
def export_csv_zip() -> bytes
def restore_from(path_or_bytes) -> None
```
- **Auto backup:** on startup, if `backups/tracker_<today>.db` does not exist, copy the database using SQLite's online backup API (`sqlite3.Connection.backup`) rather than a raw file copy, so it is consistent. Delete the oldest files beyond `keep`.
- **Cloud safety:** recommend the user point `backups/` at a OneDrive/Google Drive-synced folder (configurable via `BACKUP_DIR` in `db/connection.py`, read from an optional `config.json`).
- **Restore** validates that the file opens as SQLite and contains a `schema_version` table before replacing the DB, then runs migrations.

---

## 12. Testing plan

Use a `conftest.py` fixture that creates a temp DB, runs migrations, and yields a connection factory. Minimum required tests:

**Rollover (`test_rollover.py`)**
- Moves todo tasks with `planned_date <= from_date` and increments `rollover_count`.
- Leaves done, dropped and backlog (NULL date) tasks untouched.
- Running it twice in a row moves nothing the second time and does not double-increment.
- Close day then next-morning startup rollover yields `rollover_count == 1`, not 2.
- Missed day (no close) then startup rollover moves tasks to today with count +1.
- `is_top3` is preserved.

**Tasks (`test_tasks.py`)**
- Fourth top-3 task on one date raises `ValueError`.
- Completing sets `completed_at` and `completed_date`; un-completing clears them.
- Parent with open subtasks cannot be completed.

**Daily update (`test_daily_update.py`)**
- `close_day` stores correct `planned_count` and `completed_count`.
- Unchecked open tasks become `dropped`; checked ones move to the next day.
- Editing a closed day does not trigger a second rollover.
- Prefill includes completed task titles and session minutes.

**Stats (`test_stats.py`)**
- Streak counts consecutive days; a gap resets it; today without an update counts from yesterday.
- Empty database returns 0 / empty frames, never raises.

**Suggestions (`test_suggestions.py`)**
- Weekly goal 5h, 2h done, Thursday: minutes = `ceil(3h * 60 / 4 days)` rounded up to 5 (= 45).
- No suggestion when a task for that goal is already planned for the day.
- Paused/done goals produce no suggestions.
- Cap at 180 minutes.

**Recurring (`test_recurring.py`)**
- Weekdays rule skips Saturday and Sunday.
- Calling generate twice creates one task.
- Monthly rule on day 31 falls back to the last day in shorter months.

**Backup (`test_backup.py`)**
- `auto_backup` creates one file per day and prunes old ones.
- Restore of an invalid file is rejected and leaves the DB unchanged.

Run with `pytest -q` from the project root.

---

## 13. Implementation phases (build in this order)

> Each phase: give the agent the **prompt**, review the diff, run `pytest`, walk through the **acceptance criteria** manually, commit.

### Phase 0: Project setup (about 0.5 day)
**Build:** folder structure (Section 4), `requirements.txt`, `run.bat`, `.gitignore`, `db/connection.py` (`get_conn`, DB path, foreign keys), `db/migrations.py` (schema v1 from 6.2), `lib/dates.py`, `tests/conftest.py`, a home page that shows "Tracker is running", `README.md`.

**Prompt for the agent:**
> Read SPEC.md sections 3, 4, 5, 6 and 7.1. Implement Phase 0: create the project structure, requirements, run.bat, .gitignore, the SQLite connection helper with foreign keys on, the migration runner with schema version 1 exactly as specified, lib/dates.py, and a pytest fixture that creates a temporary migrated database. Add a minimal app.py that runs migrations on startup and shows the current date. Add tests for dates helpers and migrations (a fresh DB ends at version 1, and running migrations twice changes nothing). Do not build any other features.

**Acceptance criteria**
- [ ] Double-clicking `run.bat` opens the app in the browser with no errors
- [ ] `data/tracker.db` is created with all tables
- [ ] `pytest -q` passes
- [ ] Running the app twice does not re-create or corrupt tables

---

### Phase 1: Tasks and the Today page (about 2 days)
**Build:** `db/models.py` (Task dataclass, enums), repository functions for tasks, `services/tasks.py` (create, update, complete, uncomplete, drop, restore, set_top3, subtasks), `pages/1_Today.py` with quick add, top-3, grouped list, completed section, edit dialog, overdue section.

**Prompt for the agent:**
> Read SPEC.md sections 3, 6, 7.2 and 8.2. Implement Phase 1. Add the Task dataclass and repository functions, then services/tasks.py with the rules in 7.2 (top-3 limit of 3 per planned date, parent cannot be completed while subtasks are open, complete/uncomplete set and clear completed_at and completed_date). Build pages/1_Today.py as specified in 8.2, except skip the suggested-tasks section, the rollover warning actions and the study-session dialog for now (leave clearly marked TODO comments). Write tests in tests/test_tasks.py for every rule in section 12 (Tasks).

**Acceptance criteria**
- [ ] Add a task with one line and Enter; it appears immediately
- [ ] Ticking a task moves it to Completed; unticking restores it
- [ ] Fourth top-3 star is refused with a clear message
- [ ] Editing and dropping work; subtasks display nested
- [ ] Tasks with a past due date appear in the overdue section
- [ ] Task tests pass

---

### Phase 2: Daily update and rollover (about 2 days)
**Build:** `services/rollover.py`, `services/daily_update.py`, startup rollover call in `app.py`, `pages/2_Daily_Update.py`, rollover warning badge and the three actions on the Today page, streak on the home page.

**Prompt for the agent:**
> Read SPEC.md sections 3, 7.3, 7.4, 7.9 (update_streak only), 8.1, 8.3 and 12 (Rollover and Daily update tests). Implement Phase 2. Rollover must be idempotent exactly as described. close_day must run in a single transaction. Build pages/2_Daily_Update.py as specified. Add the rollover warning badge (rollover_count >= 3) with Break down / Reschedule / Drop actions on the Today page. Call startup rollover from app.py using the cache-keyed-by-date pattern in 8.1. Write all listed tests before finishing.

**Acceptance criteria**
- [ ] Closing a day stores the update and moves unfinished tasks to tomorrow
- [ ] Unchecked open tasks are dropped instead
- [ ] Opening the app the next morning shows carried tasks with `rollover_count == 1`
- [ ] Skip closing a day; the next day's startup moves tasks to today (count +1)
- [ ] Re-opening a closed day allows text edits with no second rollover
- [ ] Streak shows on the home page
- [ ] All rollover and daily-update tests pass

**Checkpoint:** stop here and **use the app for one full week** before continuing. Note which fields you skip and which you wish existed; adjust the spec before Phase 3.

---

### Phase 3: Learning tracker (about 2 days)
**Build:** `services/learning.py`, repository functions for learning items and sessions, `pages/3_Learning.py` (all four tabs), the "log study session" dialog on the Today page after completing a learning task, study minutes pulled into the Daily Update prefill.

**Prompt for the agent:**
> Read SPEC.md sections 3, 7.5, 8.2 (dialog behaviour) and 8.4. Implement Phase 3. The takeaway field is required and must be non-blank. When a task with category 'learning' is ticked on the Today page, open a dialog that pre-fills the linked learning item and estimated minutes and allows skipping. Add tests for log_session validation and totals_by_skill.

**Acceptance criteria**
- [ ] A session cannot be saved without a takeaway
- [ ] Completing a learning task offers the session dialog, and skipping works
- [ ] History filters by skill and date and searches takeaway text
- [ ] Daily Update study minutes match the logged sessions for the day

---

### Phase 4: Goals and suggestions (about 2 days)
**Build:** `services/goals.py`, `services/suggestions.py`, `pages/4_Goals.py`, suggested-tasks section on the Today page and in the post-close confirmation.

**Prompt for the agent:**
> Read SPEC.md sections 3, 7.6, 7.7, 8.4 (goal link on learning items), 8.5 and 12 (Suggestions tests). Implement Phase 4. Keep suggestions purely rule-based as specified: minutes = ceil(remaining_hours * 60 / days_left), rounded up to the nearest 5 and capped at 180. Suggestions are only shown and added on click, never auto-created. Write the listed tests, including the Thursday example (result 45 minutes).

**Acceptance criteria**
- [ ] Create a weekly-hours goal, log sessions, and progress and status update correctly
- [ ] A behind goal produces a suggestion on Today with a working *Add to today*
- [ ] No duplicate suggestion once a task for that goal is planned
- [ ] Paused or completed goals produce nothing

---

### Phase 5: Insights and weekly review (about 2-3 days)
**Build:** remaining `services/stats.py` functions, `pages/5_Insights.py`, `pages/6_Weekly_Review.py`.

**Prompt for the agent:**
> Read SPEC.md sections 3, 7.9, 8.6, 8.7 and 12 (Stats tests). Implement Phase 5 using pandas and plotly.express. Every chart and metric must handle an empty database without raising. week_summary must return the fields listed in 7.9. The weekly review page pre-fills read-only summary cards and saves wins/blockers/next focus with an upsert on week_start.

**Acceptance criteria**
- [ ] All charts render with real data and show "No data yet" when empty
- [ ] Completion rate uses the `daily_update` snapshot counts
- [ ] Weekly review saves and reloads; saving twice for the same week updates, not duplicates
- [ ] A Sunday review takes about 5 minutes

---

### Phase 6: Recurring tasks, safety and reminders (about 2 days)
**Build:** `services/recurring.py`, `services/backup.py`, `pages/7_Settings.py`, `reminders/notify.py`, startup hooks for backup and recurring generation.

**Prompt for the agent:**
> Read SPEC.md sections 3, 7.8, 8.8, 10, 11 and 12 (Recurring and Backup tests). Implement Phase 6. Recurring generation must be idempotent (unique index plus INSERT OR IGNORE) and must not backfill missed days. Backups must use sqlite3's backup API. Restore must validate the file, back up the current DB first, and require a confirmation checkbox. notify.py must not import Streamlit and must fail silently with a log entry. Show the schtasks commands on the Settings page with the real absolute project path filled in.

**Acceptance criteria**
- [ ] A weekday recurring task appears each weekday and never twice
- [ ] A backup file is created automatically once per day; old ones are pruned
- [ ] Restore from a backup brings data back; an invalid file is rejected
- [ ] CSV export downloads a zip with one CSV per table
- [ ] Morning and evening notifications appear via Task Scheduler; the evening one is skipped when the day is already closed

---

## 14. Definition of done (whole project)

- [ ] `run.bat` starts the app; `pytest -q` passes with no skipped tests
- [ ] The full daily loop works end to end: plan, tick, log a study session, close day, rollover, next-day view
- [ ] Backups happen automatically; restore was tested at least once
- [ ] No SQL outside `db/`; no Streamlit imports inside `services/`
- [ ] README explains setup, daily use, and how to restore a backup

---

## 15. Future enhancements (not in scope now)

- Spaced-repetition scheduling of past takeaways
- Tags and full-text search across everything
- Calendar view of days with completion colours
- PDF weekly report export
- Migration to a native window (PySide6 or CustomTkinter) reusing `db/` and `services/` unchanged
- Cloud sync (only if a second device is ever needed)

---

## 16. Quick reference: business rules cheat sheet

| Rule | Value |
|---|---|
| Max top-3 tasks per day | 3 |
| Rollover warning threshold | `rollover_count >= 3` |
| Suggestion cap | 180 min, rounded up to 5 |
| Total-hours behind threshold | 10 percentage points below expected pace |
| Weekly-hours behind rule | `week_hours < target * (day_of_week - 1) / 7` |
| Backup retention | 30 daily backups |
| Date format | `YYYY-MM-DD`, local time |
| Streak | consecutive days with a daily update, counted from today or yesterday |
