"""FastAPI backend server for Tracker application.

Directly bridges the verified SQLite repository and service layers to the
modern TypeScript Bento-Grid Single-Page Application (and provides static asset serving).
Fully secured with multi-user JWT authentication and strict tenant data isolation.
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

from fastapi import FastAPI, HTTPException, Query, Body, Response, UploadFile, File, Depends, status
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

from lib.dates import today, add_days, week_start, week_end
from db.connection import get_conn
from db.migrations import run_migrations
from db import repository as repo
from db.models import DailyUpdateForm, User
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
    auth as auth_svc,
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
# Authentication Dependency
# ---------------------------------------------------------------------------
security = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> User:
    """Extract and verify JWT bearer token, resolving the current user."""
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = credentials.credentials
    payload = auth_svc.decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        user_id = int(payload["sub"])
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    with get_conn() as conn:
        user = auth_svc.get_user_by_id(conn, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account no longer exists",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user


# ---------------------------------------------------------------------------
# Pydantic Request Models
# ---------------------------------------------------------------------------
class RegisterRequest(BaseModel):
    email: str
    password: str
    name: Optional[str] = None


class LoginRequest(BaseModel):
    email: str
    password: str


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
# Public Health Check
# ---------------------------------------------------------------------------
@app.get("/api/health")
def health_check():
    """Deployment health check probe."""
    return {"status": "ok", "app": "flux-tracker", "date": today()}


# ---------------------------------------------------------------------------
# Auth Endpoints (Public)
# ---------------------------------------------------------------------------
@app.post("/api/auth/register")
def register(req: RegisterRequest):
    """Register a new user account and return JWT session token."""
    with get_conn() as conn:
        try:
            user = auth_svc.create_user(
                conn,
                email=req.email,
                password=req.password,
                name=req.name,
            )
            token = auth_svc.create_access_token(user.id, user.email)
            return {
                "token": token,
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "name": user.name,
                },
            }
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception:
            logging.exception("Registration error")
            raise HTTPException(status_code=500, detail="Registration failed")


@app.post("/api/auth/login")
def login(req: LoginRequest):
    """Authenticate email and password, returning a JWT session token."""
    with get_conn() as conn:
        user = auth_svc.authenticate_user(conn, req.email, req.password)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        token = auth_svc.create_access_token(user.id, user.email)
        return {
            "token": token,
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name,
            },
        }


@app.get("/api/auth/me")
def get_me(current_user: User = Depends(get_current_user)):
    """Return profile details for currently authenticated user."""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "name": current_user.name,
    }


# ---------------------------------------------------------------------------
# Bento Dashboard Endpoint (Scoped to current_user)
# ---------------------------------------------------------------------------
@app.get("/api/today")
def get_today_dashboard(current_user: User = Depends(get_current_user)):
    """Return consolidated data for Today's Bento Dashboard for the current user."""
    today_iso = today()
    uid = current_user.id

    with get_conn() as conn:
        # Run rollover and recurring task generation for this user
        rollover.rollover(add_days(today_iso, -1), today_iso, conn, user_id=uid)
        rec_svc.generate_for_date(today_iso, conn)

        streak = stats.update_streak(today_iso, conn, user_id=uid)
        done_count = repo.count_completed_for_date(conn, today_iso, user_id=uid)
        todo_tasks = repo.get_todo_tasks_for_date(conn, today_iso, user_id=uid)
        done_tasks = repo.get_done_tasks_for_date(conn, today_iso, user_id=uid)
        overdue_tasks = repo.get_overdue_tasks(conn, today_iso, user_id=uid)
        top3_tasks = repo.get_top3_tasks(conn, today_iso, user_id=uid)
        study_min = repo.study_minutes_for_date(conn, today_iso, user_id=uid)
        suggestions = suggest_svc.suggest_tasks_for(today_iso, conn, user_id=uid)
        day_closed = repo.get_daily_update(conn, today_iso, user_id=uid) is not None

        # Active goals with progress
        goals = repo.get_active_goals(conn, user_id=uid)
        goals_progress = []
        for g in goals:
            prog = goal_svc.goal_progress(g.id, today_iso, conn)
            goals_progress.append({
                "goal": asdict(g),
                "progress": prog,
            })

        # Recent learning sessions for bento card
        seven_days_ago = add_days(today_iso, -7)
        recent_sessions_raw = repo.get_sessions_in_range(conn, seven_days_ago, today_iso, user_id=uid)
        recent_sessions = []
        for s in recent_sessions_raw[:5]:
            item = repo.get_learning_item(conn, s.learning_item_id, user_id=uid)
            recent_sessions.append({
                "session": asdict(s),
                "skill": item.skill if item else "Unknown",
                "resource": item.resource if item else "",
            })

        # Real weekly stats for mini-charts
        cr_series = stats.completion_rate_series(seven_days_ago, today_iso, conn, user_id=uid).to_dict(orient="records")
        skill_series = stats.study_minutes_by_skill(seven_days_ago, today_iso, conn, user_id=uid).to_dict(orient="records")

        # Attach subtasks to todo tasks
        todo_with_subtasks = []
        for t in todo_tasks:
            d = asdict(t)
            subs = repo.get_subtasks(conn, t.id, user_id=uid)
            d["subtasks"] = [asdict(sub) for sub in subs]
            todo_with_subtasks.append(d)

    return {
        "today": today_iso,
        "day_closed": day_closed,
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


# ---------------------------------------------------------------------------
# Task Endpoints (Scoped to current_user)
# ---------------------------------------------------------------------------
@app.post("/api/tasks")
def create_task(req: TaskCreateRequest, current_user: User = Depends(get_current_user)):
    today_iso = today()
    uid = current_user.id
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
            user_id=uid,
        )
        task = repo.get_task(conn, task_id, user_id=uid)
    return asdict(task) if task else {"id": task_id}


@app.post("/api/tasks/{task_id}/complete")
def complete_task(task_id: int, current_user: User = Depends(get_current_user)):
    today_iso = today()
    uid = current_user.id
    with get_conn() as conn:
        try:
            task_svc.complete(task_id, conn, today_iso, user_id=uid)
            task = repo.get_task(conn, task_id, user_id=uid)
            return {"success": True, "task": asdict(task) if task else None}
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/tasks/{task_id}/uncomplete")
def uncomplete_task(task_id: int, current_user: User = Depends(get_current_user)):
    uid = current_user.id
    with get_conn() as conn:
        task_svc.uncomplete(task_id, conn, user_id=uid)
        task = repo.get_task(conn, task_id, user_id=uid)
    return {"success": True, "task": asdict(task) if task else None}


@app.post("/api/tasks/{task_id}/top3")
def toggle_top3(task_id: int, req: TaskTop3Request, current_user: User = Depends(get_current_user)):
    uid = current_user.id
    with get_conn() as conn:
        try:
            task_svc.set_top3(task_id, req.is_top3, conn, user_id=uid)
            return {"success": True, "is_top3": req.is_top3}
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/tasks/{task_id}/drop")
def drop_task(task_id: int, current_user: User = Depends(get_current_user)):
    uid = current_user.id
    with get_conn() as conn:
        task_svc.drop(task_id, conn, user_id=uid)
    return {"success": True}


@app.put("/api/tasks/{task_id}")
def update_task(task_id: int, req: TaskUpdateRequest, current_user: User = Depends(get_current_user)):
    uid = current_user.id
    with get_conn() as conn:
        task_svc.update_task(
            task_id,
            conn,
            user_id=uid,
            title=req.title,
            priority=req.priority,
            category=req.category,
            estimated_min=req.estimated_min,
            due_date=req.due_date,
            planned_date=req.planned_date,
            notes=req.notes,
        )
        task = repo.get_task(conn, task_id, user_id=uid)
    return asdict(task) if task else {"id": task_id}


@app.post("/api/tasks/{parent_id}/subtasks")
def add_subtask(parent_id: int, req: SubtaskCreateRequest, current_user: User = Depends(get_current_user)):
    today_iso = today()
    uid = current_user.id
    with get_conn() as conn:
        parent = repo.get_task(conn, parent_id, user_id=uid)
        if not parent:
            raise HTTPException(status_code=404, detail="Parent task not found")
        sub_id = task_svc.create_task(
            conn,
            title=req.title.strip(),
            planned_date=today_iso,
            priority=parent.priority,
            category=parent.category,
            parent_task_id=parent_id,
            user_id=uid,
        )
        sub = repo.get_task(conn, sub_id, user_id=uid)
    return asdict(sub) if sub else {"id": sub_id}


# ---------------------------------------------------------------------------
# Daily Update & Reflection
# ---------------------------------------------------------------------------
@app.get("/api/daily-update")
def get_daily_update_prefill(date: Optional[str] = None, current_user: User = Depends(get_current_user)):
    target_date = date or today()
    uid = current_user.id
    with get_conn() as conn:
        prefill = du_svc.build_prefill(target_date, conn, user_id=uid)

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
def close_daily_update(req: DailyCloseRequest, current_user: User = Depends(get_current_user)):
    uid = current_user.id
    form = DailyUpdateForm(
        completed_summary=req.completed_summary,
        learned_today=req.learned_today,
        study_minutes=req.study_minutes,
        day_rating=req.day_rating,
        blockers=req.blockers,
        tomorrow_focus=req.tomorrow_focus,
    )
    with get_conn() as conn:
        saved = du_svc.close_day(req.date, form, req.carry_task_ids, conn, user_id=uid)
        # Fetch tomorrow's tasks & suggestions preview
        next_day = add_days(req.date, 1)
        tomorrow_tasks = repo.get_todo_tasks_for_date(conn, next_day, user_id=uid)
        suggestions = suggest_svc.suggest_tasks_for(next_day, conn, user_id=uid)

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
def update_daily_reflection(req: DailyUpdateRequest, current_user: User = Depends(get_current_user)):
    uid = current_user.id
    with get_conn() as conn:
        existing = repo.get_daily_update(conn, req.date, user_id=uid)
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
            user_id=uid,
        )
        updated = repo.get_daily_update(conn, req.date, user_id=uid)
    return asdict(updated) if updated else {"success": True}


# ---------------------------------------------------------------------------
# Learning Endpoints
# ---------------------------------------------------------------------------
@app.get("/api/learning")
def get_learning_data(current_user: User = Depends(get_current_user)):
    uid = current_user.id
    with get_conn() as conn:
        items = repo.get_all_learning_items(conn, user_id=uid)
        distinct_skills = repo.get_distinct_skills(conn, user_id=uid)
        goals = repo.get_all_goals(conn, user_id=uid)
    return {
        "items": [asdict(it) for it in items],
        "distinct_skills": distinct_skills,
        "goals": [asdict(g) for g in goals],
    }


@app.post("/api/learning/items")
def create_learning_item(req: LearningItemCreate, current_user: User = Depends(get_current_user)):
    uid = current_user.id
    with get_conn() as conn:
        item_id = repo.create_learning_item(
            conn,
            skill=req.skill.strip(),
            resource=req.resource.strip(),
            resource_type=req.resource_type,
            status=req.status,
            goal_id=req.goal_id,
            user_id=uid,
        )
        item = repo.get_learning_item(conn, item_id, user_id=uid)
    return asdict(item) if item else {"id": item_id}


@app.post("/api/learning/sessions")
def log_learning_session(req: LearningSessionCreate, current_user: User = Depends(get_current_user)):
    today_iso = today()
    uid = current_user.id
    with get_conn() as conn:
        try:
            sess_id = repo.create_learning_session(
                conn,
                learning_item_id=req.learning_item_id,
                session_date=req.session_date or today_iso,
                duration_min=req.duration_min,
                takeaway=req.takeaway.strip(),
                confidence=req.confidence,
                task_id=req.task_id,
                user_id=uid,
            )
            if req.task_id:
                task = repo.get_task(conn, req.task_id, user_id=uid)
                if task and task.actual_min is None:
                    repo.update_task(conn, req.task_id, user_id=uid, actual_min=req.duration_min)

            return {"success": True, "id": sess_id}
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/learning/history")
def get_learning_history(
    start: Optional[str] = None,
    end: Optional[str] = None,
    skill: Optional[str] = None,
    q: Optional[str] = None,
    current_user: User = Depends(get_current_user),
):
    today_iso = today()
    uid = current_user.id
    start_date = start or add_days(today_iso, -30)
    end_date = end or today_iso

    with get_conn() as conn:
        if q and q.strip():
            sessions = repo.search_takeaways(conn, q.strip(), user_id=uid)
        elif skill and skill != "All":
            sessions = repo.get_sessions_in_range(conn, start_date, end_date, skill=skill, user_id=uid)
        else:
            sessions = repo.get_sessions_in_range(conn, start_date, end_date, user_id=uid)

        items_map = {}
        for s in sessions:
            if s.learning_item_id not in items_map:
                it = repo.get_learning_item(conn, s.learning_item_id, user_id=uid)
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
def get_review_takeaways(current_user: User = Depends(get_current_user)):
    today_iso = today()
    uid = current_user.id
    seven_days_ago = add_days(today_iso, -7)
    with get_conn() as conn:
        old = repo.get_random_old_takeaways(conn, seven_days_ago, limit=5, user_id=uid)
    return old


# ---------------------------------------------------------------------------
# Goals Endpoints
# ---------------------------------------------------------------------------
@app.get("/api/goals")
def get_goals(current_user: User = Depends(get_current_user)):
    today_iso = today()
    uid = current_user.id
    with get_conn() as conn:
        goals = repo.get_all_goals(conn, user_id=uid)
        items = repo.get_all_learning_items(conn, user_id=uid)

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
def create_goal(req: GoalCreateRequest, current_user: User = Depends(get_current_user)):
    uid = current_user.id
    with get_conn() as conn:
        gid = repo.create_goal(
            conn,
            title=req.title.strip(),
            target_type=req.target_type,
            target_hours=req.target_hours,
            start_date=req.start_date,
            target_date=req.target_date,
            user_id=uid,
        )
        goal = repo.get_goal(conn, gid, user_id=uid)
    return asdict(goal) if goal else {"id": gid}


@app.put("/api/goals/{goal_id}")
def update_goal_status(goal_id: int, req: GoalUpdateRequest, current_user: User = Depends(get_current_user)):
    uid = current_user.id
    with get_conn() as conn:
        repo.update_goal(conn, goal_id, user_id=uid, status=req.status)
        goal = repo.get_goal(conn, goal_id, user_id=uid)
    return asdict(goal) if goal else {"id": goal_id}


# ---------------------------------------------------------------------------
# Insights & Stats Endpoints
# ---------------------------------------------------------------------------
@app.get("/api/stats")
def get_statistics(
    start: Optional[str] = None,
    end: Optional[str] = None,
    current_user: User = Depends(get_current_user),
):
    today_iso = today()
    uid = current_user.id
    start_date = start or add_days(today_iso, -30)
    end_date = end or today_iso

    with get_conn() as conn:
        streak = stats.update_streak(today_iso, conn, user_id=uid)
        avg_rat = stats.average_rating(start_date, end_date, conn, user_id=uid)
        study_sql = "SELECT COALESCE(SUM(duration_min), 0) FROM learning_session WHERE session_date BETWEEN ? AND ? AND user_id = ?"
        total_study = conn.execute(study_sql, (start_date, end_date, uid)).fetchone()[0]
        tasks_done = repo.count_done_tasks_in_range(conn, start_date, end_date, user_id=uid)

        cr_df = stats.completion_rate_series(start_date, end_date, conn, user_id=uid)
        cat_df = stats.minutes_by_category(start_date, end_date, conn, user_id=uid)
        skill_df = stats.study_minutes_by_skill(start_date, end_date, conn, user_id=uid)
        week_df = stats.study_minutes_per_week(12, today_iso, conn, user_id=uid)

        updates = repo.get_daily_updates_in_range(conn, start_date, end_date, user_id=uid)
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
def get_reviews(week: Optional[str] = None, current_user: User = Depends(get_current_user)):
    today_iso = today()
    uid = current_user.id
    target_week = week or week_start(today_iso)

    with get_conn() as conn:
        summary = stats.week_summary(target_week, conn, user_id=uid)
        current_review = repo.get_review(conn, target_week, user_id=uid)
        all_reviews = repo.get_all_reviews(conn, user_id=uid)

    return {
        "selected_week": target_week,
        "summary": summary,
        "review": asdict(current_review) if current_review else None,
        "past_reviews": [asdict(r) for r in all_reviews if r.week_start != target_week],
    }


@app.post("/api/reviews")
def save_review(req: ReviewCreateRequest, current_user: User = Depends(get_current_user)):
    uid = current_user.id
    with get_conn() as conn:
        repo.upsert_review(
            conn,
            week_start=req.week_start,
            wins=req.wins,
            blockers=req.blockers,
            next_focus=req.next_focus,
            user_id=uid,
        )
        review = repo.get_review(conn, req.week_start, user_id=uid)
    return asdict(review) if review else {"success": True}


# ---------------------------------------------------------------------------
# Settings, Backups, Recurring, Exports
# ---------------------------------------------------------------------------
SAFE_BACKUP_FILENAME_REGEX = re.compile(r"^[a-zA-Z0-9_-]+\.db$")


def validate_backup_filename(filename: str) -> str:
    """OWASP A01/A04 Path Traversal Guard."""
    if not filename or not SAFE_BACKUP_FILENAME_REGEX.match(filename):
        raise HTTPException(status_code=400, detail="Invalid filename format.")

    canonical_dir = os.path.realpath(backup.BACKUP_DIR)
    target_path = os.path.realpath(os.path.join(backup.BACKUP_DIR, filename))

    if not target_path.startswith(canonical_dir + os.sep) and target_path != canonical_dir:
        raise HTTPException(status_code=400, detail="Access denied.")

    if not os.path.isfile(target_path):
        raise HTTPException(status_code=404, detail="Requested file not found.")

    return target_path


@app.get("/api/settings")
def get_settings(current_user: User = Depends(get_current_user)):
    uid = current_user.id
    with get_conn() as conn:
        raw_backups = backup.list_backups()
        safe_backups = [
            {"name": b["name"], "size_mb": b["size_mb"], "created": b["created"]}
            for b in raw_backups
        ]
        recurring = repo.get_all_recurring_tasks(conn, user_id=uid)
        task_count = conn.execute("SELECT COUNT(*) FROM task WHERE user_id = ?", (uid,)).fetchone()[0]
        session_count = conn.execute("SELECT COUNT(*) FROM learning_session WHERE user_id = ?", (uid,)).fetchone()[0]
        goal_count = conn.execute("SELECT COUNT(*) FROM goal WHERE user_id = ?", (uid,)).fetchone()[0]
        update_count = conn.execute("SELECT COUNT(*) FROM daily_update WHERE user_id = ?", (uid,)).fetchone()[0]

    return {
        "backups": safe_backups,
        "recurring_tasks": [asdict(r) for r in recurring],
        "system_info": {
            "status": "healthy",
            "storage_engine": "SQLite",
            "sqlite_version": sqlite3.sqlite_version,
            "security_shield": "OWASP Information Disclosure Shield Active",
            "user_email": current_user.email,
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
def get_backups(current_user: User = Depends(get_current_user)):
    raw_backups = backup.list_backups()
    return [
        {"name": b["name"], "size_mb": b["size_mb"], "created": b["created"]}
        for b in raw_backups
    ]


@app.post("/api/backups")
def trigger_backup(current_user: User = Depends(get_current_user)):
    try:
        path = backup.backup_now()
        return {"success": True, "filename": os.path.basename(path)}
    except Exception:
        logging.exception("Backup creation error")
        raise HTTPException(status_code=500, detail="Failed to create backup.")


@app.get("/api/backups/{filename}/download")
def download_backup(filename: str, current_user: User = Depends(get_current_user)):
    target_path = validate_backup_filename(filename)
    return FileResponse(target_path, filename=filename, media_type="application/x-sqlite3")


@app.post("/api/backups/restore")
def restore_backup(req: BackupRestoreRequest, current_user: User = Depends(get_current_user)):
    target_path = validate_backup_filename(req.filename)
    try:
        backup.restore_from(target_path)
        return {"success": True, "message": "Database restored successfully."}
    except Exception:
        logging.exception("Database restore error")
        raise HTTPException(status_code=500, detail="Failed to restore database from backup.")


@app.post("/api/backups/upload")
async def upload_and_restore_backup(file: UploadFile = File(...), current_user: User = Depends(get_current_user)):
    if not file.filename or not file.filename.endswith(".db"):
        raise HTTPException(status_code=400, detail="File must be a SQLite .db file.")

    MAX_SIZE = 50 * 1024 * 1024
    contents = await file.read(MAX_SIZE + 1)
    if len(contents) > MAX_SIZE:
        raise HTTPException(status_code=413, detail="File too large. Maximum allowed size is 50MB.")

    if not contents.startswith(b"SQLite format 3\x00"):
        raise HTTPException(status_code=400, detail="Invalid file: Missing valid SQLite database header.")

    try:
        backup.restore_from(contents)
        return {"success": True, "message": "Database restored from uploaded backup."}
    except Exception:
        logging.exception("Uploaded database restore error")
        raise HTTPException(status_code=500, detail="Failed to restore database from uploaded file.")


# Recurring Task Endpoints
@app.get("/api/recurring")
def get_recurring_tasks(current_user: User = Depends(get_current_user)):
    uid = current_user.id
    with get_conn() as conn:
        tasks = repo.get_all_recurring_tasks(conn, user_id=uid)
    return [asdict(t) for t in tasks]


@app.post("/api/recurring")
def create_recurring_task(req: RecurringCreateRequest, current_user: User = Depends(get_current_user)):
    uid = current_user.id
    with get_conn() as conn:
        rid = repo.create_recurring_task(
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
            user_id=uid,
        )
        tasks = repo.get_all_recurring_tasks(conn, user_id=uid)
        created = next((t for t in tasks if t.id == rid), None)
    return asdict(created) if created else {"id": rid}


@app.put("/api/recurring/{rec_id}")
def update_recurring_task(rec_id: int, req: RecurringUpdateRequest, current_user: User = Depends(get_current_user)):
    uid = current_user.id
    updates = {k: v for k, v in req.model_dump().items() if v is not None}
    with get_conn() as conn:
        repo.update_recurring_task(conn, rec_id, user_id=uid, **updates)
        tasks = repo.get_all_recurring_tasks(conn, user_id=uid)
        updated = next((t for t in tasks if t.id == rec_id), None)
    return asdict(updated) if updated else {"success": True}


@app.delete("/api/recurring/{rec_id}")
def delete_recurring_task(rec_id: int, current_user: User = Depends(get_current_user)):
    uid = current_user.id
    with get_conn() as conn:
        repo.delete_recurring_task(conn, rec_id, user_id=uid)
    return {"success": True}


@app.post("/api/recurring/generate")
def generate_recurring_tasks(req: Optional[RecurringGenerateRequest] = None, current_user: User = Depends(get_current_user)):
    target_date = (req.date if req and req.date else None) or today()
    with get_conn() as conn:
        count = rec_svc.generate_for_date(target_date, conn)
    return {"success": True, "date": target_date, "generated_count": count}


# Data Export Endpoints (Scoped strictly to current user)
@app.get("/api/export/csv")
def export_csv_table(
    table: str = Query("tasks", pattern="^(tasks|sessions|updates|goals)$"),
    current_user: User = Depends(get_current_user),
):
    today_iso = today()
    uid = current_user.id
    with get_conn() as conn:
        if table == "tasks":
            rows = repo.export_table_as_dicts(conn, "task", user_id=uid)
            filename = f"flux_tasks_{today_iso}.csv"
        elif table == "sessions":
            rows = repo.export_table_as_dicts(conn, "learning_session", user_id=uid)
            filename = f"flux_sessions_{today_iso}.csv"
        elif table == "updates":
            rows = repo.export_table_as_dicts(conn, "daily_update", user_id=uid)
            filename = f"flux_daily_updates_{today_iso}.csv"
        elif table == "goals":
            rows = repo.export_table_as_dicts(conn, "goal", user_id=uid)
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


@app.get("/api/export/json")
def export_database_json(current_user: User = Depends(get_current_user)):
    today_iso = today()
    uid = current_user.id
    with get_conn() as conn:
        table_names = repo.get_all_table_names(conn)
        dump = {}
        for tbl in table_names:
            dump[tbl] = repo.export_table_as_dicts(conn, tbl, user_id=uid)

    dump["_metadata"] = {
        "exported_at": today_iso,
        "app": "flux-tracker",
        "user_email": current_user.email,
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
def get_notification_settings(current_user: User = Depends(get_current_user)):
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


# ---------------------------------------------------------------------------
# Mount Static Frontend Distribution (React + TypeScript build)
# ---------------------------------------------------------------------------
DIST_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend", "dist")

if os.path.exists(DIST_DIR):
    app.mount("/", StaticFiles(directory=DIST_DIR, html=True), name="static")
