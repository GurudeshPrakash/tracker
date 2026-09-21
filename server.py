"""FastAPI backend server for Tracker application.

Directly bridges the verified SQLite repository and service layers to the
modern TypeScript Bento-Grid Single-Page Application (and provides static asset serving).
"""

from __future__ import annotations

import os
import sys
import csv
import io
import json
import re
import logging
import sqlite3
from contextlib import asynccontextmanager
from dataclasses import asdict
from datetime import date as dt_date, timedelta
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException, Query, Body, Response, UploadFile, File
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from lib.dates import today, add_days, week_start, week_end
from db.connection import get_conn
from db.migrations import run_migrations
from db import repository as repo
from db.models import DailyUpdateForm
from services import (
    tasks as task_svc,
    daily_update as du_svc,
    learning as learn_svc,
    goals as goal_svc,
    stats,
    backup,
    recurring as rec_svc,
    rollover,
    suggestions as suggest_svc,
)

# Startup routine
@asynccontextmanager
async def lifespan(app: FastAPI):
    today_iso = today()
    with get_conn() as conn:
        run_migrations(conn)
        backup.auto_backup(today_iso)
        rec_svc.generate_for_date(today_iso, conn)
        rollover.rollover(add_days(today_iso, -1), today_iso, conn)
    yield


app = FastAPI(title="Tracker API", lifespan=lifespan)

# OWASP Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
    return response

# Allow CORS for development if needed
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Pydantic Request Models
# ---------------------------------------------------------------------------
class TaskCreateRequest(BaseModel):
    title: str
    priority: str = "medium"
    category: str = "work"
    estimated_min: Optional[int] = None
    goal_id: Optional[int] = None
    learning_item_id: Optional[int] = None
    planned_date: Optional[str] = None
    due_date: Optional[str] = None
    notes: Optional[str] = None
    parent_task_id: Optional[int] = None

class TaskUpdateRequest(BaseModel):
    title: Optional[str] = None
    priority: Optional[str] = None
    category: Optional[str] = None
    estimated_min: Optional[int] = None
    due_date: Optional[str] = None
    planned_date: Optional[str] = None
    notes: Optional[str] = None

class TaskTop3Request(BaseModel):
    is_top3: bool

class SubtaskCreateRequest(BaseModel):
    title: str

class DailyCloseRequest(BaseModel):
    date: str
    completed_summary: str = ""
    learned_today: str = ""
    study_minutes: int = 0
    day_rating: Optional[int] = None
    blockers: str = ""
    tomorrow_focus: str = ""
    carry_task_ids: List[int] = []

class DailyUpdateRequest(BaseModel):
    date: str
    completed_summary: str = ""
    learned_today: str = ""
    study_minutes: int = 0
    day_rating: Optional[int] = None
    blockers: str = ""
    tomorrow_focus: str = ""

class LearningItemCreate(BaseModel):
    skill: str
    resource: str
    resource_type: str = "course"
    status: str = "in_progress"
    goal_id: Optional[int] = None

class LearningSessionCreate(BaseModel):
    learning_item_id: int
    session_date: Optional[str] = None
    duration_min: int
    takeaway: str
    confidence: Optional[int] = None
    task_id: Optional[int] = None

class GoalCreateRequest(BaseModel):
    title: str
    target_type: str = "weekly_hours"
    target_hours: float
    start_date: str
    target_date: Optional[str] = None

class GoalUpdateRequest(BaseModel):
    status: str

class ReviewCreateRequest(BaseModel):
    week_start: str
    wins: Optional[str] = None
    blockers: Optional[str] = None
    next_focus: Optional[str] = None

class RecurringCreateRequest(BaseModel):
    title: str
    rule: str  # 'daily', 'weekdays', 'weekly', 'monthly'
    start_date: str
    priority: str = "medium"
    category: str = "work"
    goal_id: Optional[int] = None
    learning_item_id: Optional[int] = None
    estimated_min: Optional[int] = None
    weekday: Optional[int] = None
    day_of_month: Optional[int] = None
    end_date: Optional[str] = None

class RecurringUpdateRequest(BaseModel):
    title: Optional[str] = None
    rule: Optional[str] = None
    start_date: Optional[str] = None
    priority: Optional[str] = None
    category: Optional[str] = None
    goal_id: Optional[int] = None
    learning_item_id: Optional[int] = None
    estimated_min: Optional[int] = None
    weekday: Optional[int] = None
    day_of_month: Optional[int] = None
    end_date: Optional[str] = None
    active: Optional[int] = None

class BackupRestoreRequest(BaseModel):
    filename: str

class RecurringGenerateRequest(BaseModel):
    date: Optional[str] = None


# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/today")
def get_today_dashboard():
    """Return consolidated data for Today's Bento Dashboard."""
    today_iso = today()
    with get_conn() as conn:
        streak = stats.update_streak(today_iso, conn)
        done_count = repo.count_completed_for_date(conn, today_iso)
        todo_tasks = repo.get_todo_tasks_for_date(conn, today_iso)
        done_tasks = repo.get_done_tasks_for_date(conn, today_iso)
        overdue_tasks = repo.get_overdue_tasks(conn, today_iso)
        top3_tasks = repo.get_top3_tasks(conn, today_iso)
        study_min = repo.study_minutes_for_date(conn, today_iso)
        suggestions = suggest_svc.suggest_tasks_for(today_iso, conn)

        # Active goals with progress
        goals = repo.get_active_goals(conn)
        goals_progress = []
        for g in goals:
            prog = goal_svc.goal_progress(g.id, today_iso, conn)
            goals_progress.append({
                "goal": asdict(g),
                "progress": prog,
            })

        # Recent learning sessions for bento card
        seven_days_ago = add_days(today_iso, -7)
        recent_sessions_raw = repo.get_sessions_in_range(conn, seven_days_ago, today_iso)
        recent_sessions = []
        for s in recent_sessions_raw[:5]:
            item = repo.get_learning_item(conn, s.learning_item_id)
            recent_sessions.append({
                "session": asdict(s),
                "skill": item.skill if item else "Unknown",
                "resource": item.resource if item else "",
            })

        # Real weekly stats for mini-charts
        cr_series = stats.completion_rate_series(seven_days_ago, today_iso, conn).to_dict(orient="records")
        skill_series = stats.study_minutes_by_skill(seven_days_ago, today_iso, conn).to_dict(orient="records")

        # Attach subtasks to todo tasks
        todo_with_subtasks = []
        for t in todo_tasks:
            d = asdict(t)
            subs = repo.get_subtasks(conn, t.id)
            d["subtasks"] = [asdict(sub) for sub in subs]
            todo_with_subtasks.append(d)

    return {
        "today": today_iso,
        "streak": streak,
        "done_count": done_count,
        "planned_count": len(todo_tasks) + done_count,
        "study_min": study_min,
        "top3": [asdict(t) for t in top3_tasks],
        "tasks": todo_with_subtasks,
        "completed": [asdict(t) for t in done_tasks],
        "overdue": [asdict(t) for t in overdue_tasks],
        "suggestions": [asdict(s) for s in suggestions],
        "goals": goals_progress,
        "recent_sessions": recent_sessions,
        "completion_series": cr_series,
        "skill_series": skill_series,
    }


@app.get("/api/health")
def health_check():
    """Deployment health check probe."""
    return {"status": "ok", "app": "flux-tracker", "date": today()}


@app.post("/api/tasks")
def create_task(req: TaskCreateRequest):
    today_iso = today()
    with get_conn() as conn:
        task_id = task_svc.create_task(
            conn,
            title=req.title.strip(),
            planned_date=req.planned_date or today_iso,
            priority=req.priority,
            category=req.category,
            estimated_min=req.estimated_min,
            goal_id=req.goal_id,
            learning_item_id=req.learning_item_id,
            notes=req.notes,
            due_date=req.due_date,
            parent_task_id=req.parent_task_id,
        )
        task = repo.get_task(conn, task_id)
    return asdict(task) if task else {"id": task_id}


@app.post("/api/tasks/{task_id}/complete")
def complete_task(task_id: int):
    today_iso = today()
    with get_conn() as conn:
        try:
            task_svc.complete(task_id, conn, today_iso)
            task = repo.get_task(conn, task_id)
            return {"success": True, "task": asdict(task) if task else None}
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/tasks/{task_id}/uncomplete")
def uncomplete_task(task_id: int):
    with get_conn() as conn:
        task_svc.uncomplete(task_id, conn)
        task = repo.get_task(conn, task_id)
    return {"success": True, "task": asdict(task) if task else None}


@app.post("/api/tasks/{task_id}/top3")
def toggle_top3(task_id: int, req: TaskTop3Request):
    with get_conn() as conn:
        try:
            task_svc.set_top3(task_id, req.is_top3, conn)
            return {"success": True, "is_top3": req.is_top3}
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/tasks/{task_id}/drop")
def drop_task(task_id: int):
    with get_conn() as conn:
        task_svc.drop(task_id, conn)
    return {"success": True}


@app.put("/api/tasks/{task_id}")
def update_task(task_id: int, req: TaskUpdateRequest):
    with get_conn() as conn:
        task_svc.update_task(
            task_id,
            conn,
            title=req.title,
            priority=req.priority,
            category=req.category,
            estimated_min=req.estimated_min,
            due_date=req.due_date,
            planned_date=req.planned_date,
            notes=req.notes,
        )
        task = repo.get_task(conn, task_id)
    return asdict(task) if task else {"id": task_id}


@app.post("/api/tasks/{parent_id}/subtasks")
def add_subtask(parent_id: int, req: SubtaskCreateRequest):
    today_iso = today()
    with get_conn() as conn:
        parent = repo.get_task(conn, parent_id)
        if not parent:
            raise HTTPException(status_code=404, detail="Parent task not found")
        sub_id = task_svc.create_task(
            conn,
            title=req.title.strip(),
            planned_date=today_iso,
            priority=parent.priority,
            category=parent.category,
            parent_task_id=parent_id,
        )
        sub = repo.get_task(conn, sub_id)
    return asdict(sub) if sub else {"id": sub_id}


# ---------------------------------------------------------------------------
# Daily Update & Reflection
# ---------------------------------------------------------------------------

@app.get("/api/daily-update")
def get_daily_update_prefill(date: Optional[str] = None):
    target_date = date or today()
    with get_conn() as conn:
        prefill = du_svc.build_prefill(target_date, conn)

        return {
            "date": target_date,
            "completed_tasks": [asdict(t) for t in prefill["completed_tasks"]],
            "open_tasks": [asdict(t) for t in prefill["open_tasks"]],
            "study_minutes": prefill["study_minutes"],
            "session_takeaways": prefill["session_takeaways"],
            "existing": asdict(prefill["existing"]) if prefill["existing"] else None,
            "is_closed": prefill["existing"] is not None,
        }


@app.post("/api/daily-update/close")
def close_daily_update(req: DailyCloseRequest):
    form = DailyUpdateForm(
        completed_summary=req.completed_summary,
        learned_today=req.learned_today,
        study_minutes=req.study_minutes,
        day_rating=req.day_rating,
        blockers=req.blockers,
        tomorrow_focus=req.tomorrow_focus,
    )
    with get_conn() as conn:
        saved = du_svc.close_day(req.date, form, req.carry_task_ids, conn)
        # Fetch tomorrow's tasks & suggestions preview
        next_day = add_days(req.date, 1)
        tomorrow_tasks = repo.get_todo_tasks_for_date(conn, next_day)
        suggestions = suggest_svc.suggest_tasks_for(next_day, conn)

    return {
        "success": True,
        "saved": asdict(saved),
        "tomorrow": {
            "date": next_day,
            "tasks": [asdict(t) for t in tomorrow_tasks],
            "suggestions": [asdict(s) for s in suggestions],
        },
    }


@app.put("/api/daily-update")
def update_daily_reflection(req: DailyUpdateRequest):
    with get_conn() as conn:
        existing = repo.get_daily_update(conn, req.date)
        if not existing:
            raise HTTPException(status_code=404, detail="Daily update not found for date")
        repo.upsert_daily_update(
            conn,
            date=req.date,
            planned_count=existing.planned_count,
            completed_count=existing.completed_count,
            completed_summary=req.completed_summary,
            learned_today=req.learned_today,
            study_minutes=req.study_minutes,
            day_rating=req.day_rating,
            blockers=req.blockers,
            tomorrow_focus=req.tomorrow_focus,
        )
        updated = repo.get_daily_update(conn, req.date)
    return asdict(updated) if updated else {"success": True}


# ---------------------------------------------------------------------------
# Learning Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/learning")
def get_learning_data():
    with get_conn() as conn:
        items = repo.get_all_learning_items(conn)
        distinct_skills = repo.get_distinct_skills(conn)
        goals = repo.get_all_goals(conn)
    return {
        "items": [asdict(it) for it in items],
        "distinct_skills": distinct_skills,
        "goals": [asdict(g) for g in goals],
    }


@app.post("/api/learning/items")
def create_learning_item(req: LearningItemCreate):
    with get_conn() as conn:
        item_id = repo.create_learning_item(
            conn,
            skill=req.skill.strip(),
            resource=req.resource.strip(),
            resource_type=req.resource_type,
            status=req.status,
            goal_id=req.goal_id,
        )
        item = repo.get_learning_item(conn, item_id)
    return asdict(item) if item else {"id": item_id}


@app.post("/api/learning/sessions")
def log_learning_session(req: LearningSessionCreate):
    today_iso = today()
    with get_conn() as conn:
        try:
            sess_id = learn_svc.log_session(
                item_id=req.learning_item_id,
                session_date=req.session_date or today_iso,
                duration_min=req.duration_min,
                takeaway=req.takeaway.strip(),
                confidence=req.confidence,
                task_id=req.task_id,
                conn=conn,
            )
            return {"success": True, "id": sess_id}
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/learning/history")
def get_learning_history(
    start: Optional[str] = None,
    end: Optional[str] = None,
    skill: Optional[str] = None,
    q: Optional[str] = None,
):
    today_iso = today()
    start_date = start or add_days(today_iso, -30)
    end_date = end or today_iso

    with get_conn() as conn:
        if q and q.strip():
            sessions = repo.search_takeaways(conn, q.strip())
        elif skill and skill != "All":
            sessions = repo.get_sessions_in_range(conn, start_date, end_date, skill=skill)
        else:
            sessions = repo.get_sessions_in_range(conn, start_date, end_date)

        items_map = {}
        for s in sessions:
            if s.learning_item_id not in items_map:
                it = repo.get_learning_item(conn, s.learning_item_id)
                items_map[s.learning_item_id] = it

        results = []
        for s in sessions:
            it = items_map.get(s.learning_item_id)
            results.append({
                "session": asdict(s),
                "skill": it.skill if it else "Unknown",
                "resource": it.resource if it else "",
            })

    return results


@app.get("/api/learning/review")
def get_review_takeaways():
    today_iso = today()
    seven_days_ago = add_days(today_iso, -7)
    with get_conn() as conn:
        old = repo.get_random_old_takeaways(conn, seven_days_ago, limit=5)
    return old


# ---------------------------------------------------------------------------
# Goals Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/goals")
def get_goals():
    today_iso = today()
    with get_conn() as conn:
        goals = repo.get_all_goals(conn)
        items = repo.get_all_learning_items(conn)

        results = []
        for g in goals:
            prog = goal_svc.goal_progress(g.id, today_iso, conn)
            linked = [asdict(it) for it in items if it.goal_id == g.id]
            results.append({
                "goal": asdict(g),
                "progress": prog,
                "linked_resources": linked,
            })
    return results


@app.post("/api/goals")
def create_goal(req: GoalCreateRequest):
    with get_conn() as conn:
        gid = repo.create_goal(
            conn,
            title=req.title.strip(),
            target_type=req.target_type,
            target_hours=req.target_hours,
            start_date=req.start_date,
            target_date=req.target_date,
        )
        goal = repo.get_goal(conn, gid)
    return asdict(goal) if goal else {"id": gid}


@app.put("/api/goals/{goal_id}")
def update_goal_status(goal_id: int, req: GoalUpdateRequest):
    with get_conn() as conn:
        repo.update_goal(conn, goal_id, status=req.status)
        goal = repo.get_goal(conn, goal_id)
    return asdict(goal) if goal else {"id": goal_id}


# ---------------------------------------------------------------------------
# Insights & Stats Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/stats")
def get_statistics(start: Optional[str] = None, end: Optional[str] = None):
    today_iso = today()
    start_date = start or add_days(today_iso, -30)
    end_date = end or today_iso

    with get_conn() as conn:
        streak = stats.update_streak(today_iso, conn)
        avg_rat = stats.average_rating(start_date, end_date, conn)
        total_study = conn.execute(
            "SELECT COALESCE(SUM(duration_min), 0) FROM learning_session WHERE session_date BETWEEN ? AND ?",
            (start_date, end_date),
        ).fetchone()[0]
        tasks_done = repo.count_done_tasks_in_range(conn, start_date, end_date)

        # Dataframe serializations
        cr_df = stats.completion_rate_series(start_date, end_date, conn)
        cat_df = stats.minutes_by_category(start_date, end_date, conn)
        skill_df = stats.study_minutes_by_skill(start_date, end_date, conn)
        week_df = stats.study_minutes_per_week(12, today_iso, conn)

        updates = repo.get_daily_updates_in_range(conn, start_date, end_date)
        ratings = [{"date": u.date, "rating": u.day_rating} for u in updates if u.day_rating]

    return {
        "streak": streak,
        "avg_rating": avg_rat,
        "total_study_min": total_study,
        "tasks_completed": tasks_done,
        "completion_rate_series": cr_df.to_dict(orient="records"),
        "minutes_by_category": cat_df.to_dict(orient="records"),
        "study_minutes_by_skill": skill_df.to_dict(orient="records"),
        "study_minutes_per_week": week_df.to_dict(orient="records"),
        "day_ratings": ratings,
    }


# ---------------------------------------------------------------------------
# Weekly Review Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/reviews")
def get_reviews(week: Optional[str] = None):
    today_iso = today()
    target_week = week or week_start(today_iso)

    with get_conn() as conn:
        summary = stats.week_summary(target_week, conn)
        current_review = repo.get_review(conn, target_week)
        all_reviews = repo.get_all_reviews(conn)

    return {
        "selected_week": target_week,
        "summary": summary,
        "review": asdict(current_review) if current_review else None,
        "past_reviews": [asdict(r) for r in all_reviews if r.week_start != target_week],
    }


@app.post("/api/reviews")
def save_review(req: ReviewCreateRequest):
    with get_conn() as conn:
        repo.upsert_review(
            conn,
            week_start=req.week_start,
            wins=req.wins,
            blockers=req.blockers,
            next_focus=req.next_focus,
        )
        review = repo.get_review(conn, req.week_start)
    return asdict(review) if review else {"success": True}


# ---------------------------------------------------------------------------
# Settings, Backups, Recurring, Exports & Automation (OWASP Hardened)
# ---------------------------------------------------------------------------

SAFE_BACKUP_FILENAME_REGEX = re.compile(r"^[a-zA-Z0-9_-]+\.db$")


def validate_backup_filename(filename: str) -> str:
    """OWASP A01/A04 Path Traversal Guard:
    Ensure filename contains strictly valid characters and resolves strictly inside BACKUP_DIR.
    """
    if not filename or not SAFE_BACKUP_FILENAME_REGEX.match(filename):
        raise HTTPException(status_code=400, detail="Invalid filename format.")

    canonical_dir = os.path.realpath(backup.BACKUP_DIR)
    target_path = os.path.realpath(os.path.join(backup.BACKUP_DIR, filename))

    # Path traversal check: resolved path must be inside canonical backup directory
    if not target_path.startswith(canonical_dir + os.sep) and target_path != canonical_dir:
        raise HTTPException(status_code=400, detail="Access denied.")

    if not os.path.isfile(target_path):
        raise HTTPException(status_code=404, detail="Requested file not found.")

    return target_path


@app.get("/api/settings")
def get_settings():
    with get_conn() as conn:
        raw_backups = backup.list_backups()
        # OWASP CWE-200: Redact absolute host filesystem paths
        safe_backups = [
            {"name": b["name"], "size_mb": b["size_mb"], "created": b["created"]}
            for b in raw_backups
        ]
        recurring = rec_svc.get_all(conn)
        task_count = conn.execute("SELECT COUNT(*) FROM task").fetchone()[0]
        session_count = conn.execute("SELECT COUNT(*) FROM learning_session").fetchone()[0]
        goal_count = conn.execute("SELECT COUNT(*) FROM goal").fetchone()[0]
        update_count = conn.execute("SELECT COUNT(*) FROM daily_update").fetchone()[0]

    return {
        "backups": safe_backups,
        "recurring_tasks": [asdict(r) for r in recurring],
        "system_info": {
            "status": "healthy",
            "storage_engine": "SQLite",
            "sqlite_version": sqlite3.sqlite_version,
            "security_shield": "OWASP Information Disclosure Shield Active",
            "table_counts": {
                "tasks": task_count,
                "sessions": session_count,
                "goals": goal_count,
                "updates": update_count,
                "recurring": len(recurring),
            },
        },
    }


@app.get("/api/backups")
def get_backups():
    raw_backups = backup.list_backups()
    # OWASP CWE-200: Redact absolute host filesystem paths
    return [
        {"name": b["name"], "size_mb": b["size_mb"], "created": b["created"]}
        for b in raw_backups
    ]


@app.post("/api/backups")
def trigger_backup():
    try:
        path = backup.backup_now()
        return {"success": True, "filename": os.path.basename(path)}
    except Exception as e:
        logging.error(f"Backup creation error: {e}")
        raise HTTPException(status_code=500, detail="Failed to create backup.")


@app.get("/api/backups/{filename}/download")
def download_backup(filename: str):
    target_path = validate_backup_filename(filename)
    return FileResponse(target_path, filename=filename, media_type="application/x-sqlite3")


@app.post("/api/backups/restore")
def restore_backup(req: BackupRestoreRequest):
    target_path = validate_backup_filename(req.filename)
    try:
        backup.restore_from(target_path)
        return {"success": True, "message": "Database restored successfully."}
    except Exception as e:
        logging.error(f"Database restore error: {e}")
        raise HTTPException(status_code=500, detail="Failed to restore database from backup.")


@app.post("/api/backups/upload")
async def upload_and_restore_backup(file: UploadFile = File(...)):
    # 1. Filename validation
    if not file.filename or not file.filename.endswith(".db"):
        raise HTTPException(status_code=400, detail="File must be a SQLite .db file.")

    # 2. Maximum file size check (50 MB limit to prevent Denial of Service)
    MAX_SIZE = 50 * 1024 * 1024
    contents = await file.read(MAX_SIZE + 1)
    if len(contents) > MAX_SIZE:
        raise HTTPException(status_code=413, detail="File too large. Maximum allowed size is 50MB.")

    # 3. Magic header validation: SQLite database header starts with 'SQLite format 3\x00'
    if not contents.startswith(b"SQLite format 3\x00"):
        raise HTTPException(status_code=400, detail="Invalid file: Missing valid SQLite database header.")

    try:
        backup.restore_from(contents)
        return {"success": True, "message": "Database restored from uploaded backup."}
    except Exception as e:
        logging.error(f"Uploaded database restore error: {e}")
        raise HTTPException(status_code=500, detail="Failed to restore database from uploaded file.")



# Recurring Task Endpoints
@app.get("/api/recurring")
def get_recurring_tasks():
    with get_conn() as conn:
        tasks = rec_svc.get_all(conn)
    return [asdict(t) for t in tasks]


@app.post("/api/recurring")
def create_recurring_task(req: RecurringCreateRequest):
    with get_conn() as conn:
        rid = rec_svc.create(
            conn,
            title=req.title.strip(),
            rule=req.rule,
            start_date=req.start_date,
            priority=req.priority,
            category=req.category,
            goal_id=req.goal_id,
            learning_item_id=req.learning_item_id,
            estimated_min=req.estimated_min,
            weekday=req.weekday,
            day_of_month=req.day_of_month,
            end_date=req.end_date,
        )
        tasks = rec_svc.get_all(conn)
        created = next((t for t in tasks if t.id == rid), None)
    return asdict(created) if created else {"id": rid}


@app.put("/api/recurring/{rec_id}")
def update_recurring_task(rec_id: int, req: RecurringUpdateRequest):
    updates = {k: v for k, v in req.model_dump().items() if v is not None}
    with get_conn() as conn:
        rec_svc.update(conn, rec_id, **updates)
        tasks = rec_svc.get_all(conn)
        updated = next((t for t in tasks if t.id == rec_id), None)
    return asdict(updated) if updated else {"success": True}


@app.delete("/api/recurring/{rec_id}")
def delete_recurring_task(rec_id: int):
    with get_conn() as conn:
        rec_svc.delete(conn, rec_id)
    return {"success": True}


@app.post("/api/recurring/generate")
def generate_recurring_tasks(req: Optional[RecurringGenerateRequest] = None):
    target_date = (req.date if req and req.date else None) or today()
    with get_conn() as conn:
        count = rec_svc.generate_for_date(target_date, conn)
    return {"success": True, "date": target_date, "generated_count": count}


# Data Export Endpoints
@app.get("/api/export/csv")
def export_csv_table(table: str = Query("tasks", regex="^(tasks|sessions|updates|goals)$")):
    today_iso = today()
    with get_conn() as conn:
        if table == "tasks":
            rows = repo.export_table_as_dicts(conn, "task")
            filename = f"flux_tasks_{today_iso}.csv"
        elif table == "sessions":
            rows = repo.export_table_as_dicts(conn, "learning_session")
            filename = f"flux_sessions_{today_iso}.csv"
        elif table == "updates":
            rows = repo.export_table_as_dicts(conn, "daily_update")
            filename = f"flux_daily_updates_{today_iso}.csv"
        elif table == "goals":
            rows = repo.export_table_as_dicts(conn, "goal")
            filename = f"flux_goals_{today_iso}.csv"
        else:
            rows = []
            filename = f"flux_export_{today_iso}.csv"

    out = io.StringIO()
    if rows:
        writer = csv.DictWriter(out, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    else:
        out.write("No records found\n")

    return Response(
        content=out.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.get("/api/export/zip")
def export_all_tables_zip():
    today_iso = today()
    zip_bytes = backup.export_csv_zip()
    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="flux_complete_export_{today_iso}.zip"'},
    )


@app.get("/api/export/json")
def export_database_json():
    today_iso = today()
    with get_conn() as conn:
        table_names = repo.get_all_table_names(conn)
        dump = {}
        for tbl in table_names:
            dump[tbl] = repo.export_table_as_dicts(conn, tbl)

    dump["_metadata"] = {
        "exported_at": today_iso,
        "app": "flux-tracker",
        "format": "json_relational_export",
    }
    json_str = json.dumps(dump, indent=2, default=str)
    return Response(
        content=json_str,
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="flux_database_dump_{today_iso}.json"'},
    )


# Desktop Notifications & Task Scheduler Setup
@app.get("/api/settings/notifications")
def get_notification_settings():
    # Portable scheduled task commands using standard Windows environment execution
    morning_cmd = 'schtasks /create /tn "FluxTracker_Morning" /tr "python \"%CD%\\reminders\\notify.py\" morning" /sc daily /st 09:00 /f'
    evening_cmd = 'schtasks /create /tn "FluxTracker_Evening" /tr "python \"%CD%\\reminders\\notify.py\" evening" /sc daily /st 21:00 /f'

    root = os.path.dirname(os.path.abspath(__file__))
    log_path = os.path.join(root, "data", "notify.log")
    recent_logs = []
    if os.path.exists(log_path):
        try:
            with open(log_path, "r", encoding="utf-8") as f:
                lines = [line.strip() for line in f.readlines() if line.strip()][-15:]
                for line in lines:
                    # OWASP CWE-200: Redact absolute host filesystem paths like D:\... or C:\...
                    clean_line = re.sub(r"[A-Za-z]:\\[^:\s]+", "[REDACTED_PATH]", line)
                    recent_logs.append(clean_line)
        except Exception:
            pass

    return {
        "morning_time": "09:00",
        "evening_time": "21:00",
        "schtasks_morning_cmd": morning_cmd,
        "schtasks_evening_cmd": evening_cmd,
        "recent_logs": recent_logs,
    }



@app.post("/api/settings/test-notification")
def trigger_test_notification(mode: str = Query("morning", regex="^(morning|evening)$")):
    try:
        from plyer import notification
        from reminders.notify import _get_morning_message, _get_evening_message

        if mode == "morning":
            title, message = _get_morning_message()
        else:
            res = _get_evening_message()
            if res is None:
                title, message = "🌙 Close Your Day", "Notice: Day is already closed, but testing toast works!"
            else:
                title, message = res

        notification.notify(title=title, message=message, timeout=10)
        return {"success": True, "mode": mode, "title": title, "message": message}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Notification error: {str(e)}")



# ---------------------------------------------------------------------------
# Mount Static Frontend Distribution (React + TypeScript build)
# ---------------------------------------------------------------------------
DIST_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend", "dist")

if os.path.exists(DIST_DIR):
    app.mount("/", StaticFiles(directory=DIST_DIR, html=True), name="static")
