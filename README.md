# Daily Work & Self-Learning Tracker

A personal productivity system that runs a daily loop:

**Morning: plan the day → During the day: tick off tasks → Evening: close the day → Unfinished work rolls to tomorrow → Goals suggest what to study next.**

## Setup

### Prerequisites
- Python 3.11+
- Windows PC

### First-time setup (PowerShell)
```powershell
cd tracker
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### Running the app
Double-click `run.bat` or:
```powershell
.venv\Scripts\activate
streamlit run app.py
```

The app opens in your browser at `http://localhost:8501`.

## Features

### Currently Working
- ✅ Database setup with automatic migrations
- ✅ Task management with priorities, categories, subtasks
- ✅ Top-3 daily priorities (max 3 per day)
- ✅ Daily update with end-of-day close-out
- ✅ Automatic rollover of unfinished tasks
- ✅ Learning tracker: skills, sessions, takeaways, confidence
- ✅ Goals with progress tracking and status
- ✅ Rule-based task suggestions for behind goals
- ✅ Insights with charts (completion rate, study time, ratings)
- ✅ Weekly review
- ✅ Recurring tasks (daily, weekdays, weekly, monthly)
- ✅ Automatic backups and CSV export
- ✅ Desktop reminders via Windows Task Scheduler

## Daily Use

1. **Morning**: Open the app → see your tasks for today → add new ones
2. **During the day**: Check off tasks as you complete them → log study sessions
3. **Evening**: Click "Close my day" → fill in the update → unfinished tasks roll to tomorrow
4. **Weekly**: Review your week on the Weekly Review page

## Data

- Database: `data/tracker.db` (auto-created, git-ignored)
- Backups: `backups/` (auto-created daily, 30-day retention)

## Restoring a Backup

1. Go to Settings page
2. Select a backup file
3. Check the confirmation box
4. Click Restore

The current database is automatically backed up before any restore.

## Tests

```powershell
.venv\Scripts\activate
pytest -q
```
