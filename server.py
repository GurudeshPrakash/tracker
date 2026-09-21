"""FastAPI server exposing Tracker services for the TypeScript frontend."""

from contextlib import asynccontextmanager
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from db.connection import get_conn, init_db
from db import repository as repo
from lib import dates
from services import (
    tasks as task_svc,
    rollover as rollover_svc,
    daily_update as daily_svc,
    suggestions as sugg_svc,
    stats as stats_svc,
    goals as goals_svc,
    recurring as rec_svc,
    backup as backup_svc,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    today_iso = dates.today()
    yesterday_iso = dates.add_days(today_iso, -1)
    backup_svc.auto_backup(today_iso)
    with get_conn() as conn:
        rollover_svc.rollover(yesterday_iso, today_iso, conn)
        rec_svc.generate_for_date(today_iso, conn)
    yield


app = FastAPI(title="Tracker API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Request Models ---
class TaskCreateRequest(BaseModel):
    title: str
    planned_date: Optional[str] = None
    category: str = "work"
    priority: str = "medium"
    estimate_min: Optional[int] = None
    notes: Optional[str] = None
    goal_id: Optional[int] = None
    is_top3: bool = False


class TaskUpdateRequest(BaseModel):
    title: Optional[str] = None
    planned_date: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[str] = None
    estimated_min: Optional[int] = None
    actual_min: Optional[int] = None
    notes: Optional[str] = None
    status: Optional[str] = None


class SubtaskCreateRequest(BaseModel):
    title: str


class SessionCreateRequest(BaseModel):
    skill_id: int
    duration_min: int
    takeaway: str
    session_date: Optional[str] = None
    quality_rating: Optional[int] = None
    confidence: Optional[int] = None


class GoalCreateRequest(BaseModel):
    title: str
    category: str = "work"
    target_hours: Optional[float] = None
    target_date: Optional[str] = None
    weekly_hours_target: Optional[float] = None
    notes: Optional[str] = None


class CloseDayRequest(BaseModel):
    report_date: str
    carry_task_ids: List[int] = []
    drop_task_ids: List[int] = []
    wins: Optional[str] = None
    blockers: Optional[str] = None
    focus_tomorrow: Optional[str] = None
    mood_rating: Optional[int] = None
    productivity_rating: Optional[int] = None


# --- Endpoints ---


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/tasks")
def get_tasks(date: Optional[str] = None):
    cur_date = date or dates.today()
    with get_conn() as conn:
        groups = task_svc.get_tasks_for_today(conn, cur_date)
        all_today = groups["top3"] + groups["other_high"] + groups["other_medium"] + groups["other_low"]

        def format_task(t):
            subtasks = repo.get_subtasks(conn, t.id)
            return {
                "id": t.id,
                "title": t.title,
                "planned_date": t.planned_date,
                "category": t.category.capitalize() if t.category else "Work",
                "priority": t.priority.capitalize() if t.priority else "Medium",
                "status": t.status,
                "is_top3": bool(t.is_top3),
                "estimate_min": t.estimated_min,
                "actual_min": t.actual_min,
                "notes": t.notes,
                "rollover_count": t.rollover_count,
                "completed_at": t.completed_at,
                "subtasks": [
                    {"id": s.id, "title": s.title, "status": s.status}
                    for s in subtasks
                ],
            }

        # Structure for Prodify reference design:
        # Top-3 or in-progress tasks go to in_progress
        in_progress = [format_task(t) for t in groups["top3"]]
        other_todo = [
            format_task(t)
            for t in groups["other_high"] + groups["other_medium"] + groups["other_low"]
        ]

        if not in_progress and other_todo:
            in_progress.append(other_todo.pop(0))

        completed = [format_task(t) for t in groups["completed"]]
        overdue = [format_task(t) for t in groups["overdue"]]

        return {
            "today": cur_date,
            "in_progress": in_progress,
            "todo": other_todo,
            "completed": completed,
            "overdue": overdue,
            "backlog": [],
        }


@app.post("/api/tasks")
def create_task(req: TaskCreateRequest):
    planned_date = req.planned_date or dates.today()
    try:
        with get_conn() as conn:
            task_id = task_svc.create_task(
                conn,
                title=req.title,
                planned_date=planned_date,
                category=req.category.lower(),
                priority=req.priority.lower(),
                estimated_min=req.estimate_min,
                notes=req.notes,
                goal_id=req.goal_id,
            )
            if req.is_top3:
                try:
                    task_svc.set_top3(task_id, True, conn)
                except ValueError:
                    pass
            return {"id": task_id, "success": True}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.put("/api/tasks/{task_id}/complete")
def toggle_task_complete(task_id: int):
    try:
        with get_conn() as conn:
            task = repo.get_task(conn, task_id)
            if not task:
                raise HTTPException(status_code=404, detail="Task not found")
            if task.status == "done":
                task_svc.uncomplete(task_id, conn)
                return {"status": "todo"}
            else:
                task_svc.complete(task_id, conn)
                return {"status": "done"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.put("/api/tasks/{task_id}/top3")
def toggle_task_top3(task_id: int):
    try:
        with get_conn() as conn:
            task = repo.get_task(conn, task_id)
            if not task:
                raise HTTPException(status_code=404, detail="Task not found")
            new_val = not bool(task.is_top3)
            task_svc.set_top3(task_id, new_val, conn)
            return {"is_top3": new_val}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.put("/api/tasks/{task_id}")
def update_task(task_id: int, req: TaskUpdateRequest):
    updates = {k: v for k, v in req.model_dump().items() if v is not None}
    with get_conn() as conn:
        task_svc.update_task(task_id, conn, **updates)
    return {"success": True}


@app.delete("/api/tasks/{task_id}")
def delete_task(task_id: int):
    with get_conn() as conn:
        task_svc.drop(task_id, conn)
    return {"success": True}


@app.post("/api/tasks/{task_id}/subtasks")
def add_subtask(task_id: int, req: SubtaskCreateRequest):
    with get_conn() as conn:
        sub_id = repo.create_subtask(conn, task_id, req.title)
    return {"id": sub_id, "success": True}


@app.put("/api/subtasks/{subtask_id}/complete")
def toggle_subtask(subtask_id: int):
    with get_conn() as conn:
        sub = repo.get_subtask(conn, subtask_id)
        if not sub:
            raise HTTPException(status_code=404, detail="Subtask not found")
        if sub.status == "done":
            repo.uncomplete_subtask(conn, subtask_id)
            new_status = "todo"
        else:
            repo.complete_subtask(conn, subtask_id)
            new_status = "done"
    return {"status": new_status}


@app.get("/api/suggestions")
def get_suggestions(date: Optional[str] = None):
    cur_date = date or dates.today()
    with get_conn() as conn:
        suggs = sugg_svc.suggest_learning_task(conn, cur_date)
        if not suggs:
            return []
        # Return as list of suggestion items
        return [
            {
                "goal_id": suggs.get("goal_id"),
                "goal_title": suggs.get("goal_title", "General Learning"),
                "title": suggs["title"],
                "category": "Learning",
                "duration_min": suggs.get("estimated_min", 45),
                "reason": suggs.get("reason", "Weekly target pace"),
                "planned_date": cur_date,
            }
        ]


@app.post("/api/suggestions/accept")
def accept_suggestion(sugg: Dict[str, Any]):
    cur_date = sugg.get("planned_date") or dates.today()
    with get_conn() as conn:
        task_id = task_svc.create_task(
            conn,
            title=sugg["title"],
            planned_date=cur_date,
            category="learning",
            estimated_min=sugg.get("duration_min", 45),
            goal_id=sugg.get("goal_id"),
        )
    return {"id": task_id, "success": True}


@app.get("/api/goals")
def get_goals():
    with get_conn() as conn:
        all_goals = repo.get_all_goals(conn)
        res = []
        for g in all_goals:
            logged_min = goals_svc.get_goal_minutes(conn, g.id)
            res.append(
                {
                    "id": g.id,
                    "title": g.title,
                    "category": g.category.capitalize() if g.category else "Work",
                    "status": g.status,
                    "target_hours": g.target_hours,
                    "target_date": g.target_date,
                    "weekly_hours_target": g.weekly_target_hours,
                    "logged_minutes": logged_min,
                    "progress_pct": round((logged_min / (g.target_hours * 60) * 100), 1) if g.target_hours else 0,
                    "resources": [],
                }
            )
        return res


@app.post("/api/goals")
def create_goal(req: GoalCreateRequest):
    with get_conn() as conn:
        goal_id = repo.create_goal(
            conn,
            title=req.title,
            category=req.category.lower(),
            target_hours=req.target_hours,
            target_date=req.target_date,
            weekly_target_hours=req.weekly_hours_target,
            notes=req.notes,
        )
    return {"id": goal_id, "success": True}


@app.get("/api/learning")
def get_learning():
    today = dates.today()
    with get_conn() as conn:
        skills = repo.get_all_skills(conn)
        items = repo.get_all_learning_items(conn)
        reviews = repo.get_learning_review_items(conn, today)

        # Recent sessions
        rows = conn.execute(
            """SELECT ls.*, li.skill FROM learning_session ls
               JOIN learning_item li ON ls.learning_item_id = li.id
               ORDER BY session_date DESC LIMIT 20"""
        ).fetchall()

        return {
            "skills": [
                {
                    "id": idx + 1,
                    "name": s,
                    "category": "Development",
                    "proficiency": "Active",
                }
                for idx, s in enumerate(skills)
            ],
            "resources": [
                {
                    "id": it.id,
                    "title": it.resource,
                    "type": it.resource_type,
                    "skill": it.skill,
                }
                for it in items
            ],
            "sessions": [
                {
                    "id": r["id"],
                    "skill_id": r["learning_item_id"],
                    "duration_min": r["duration_min"],
                    "takeaway": r["takeaway"],
                    "session_date": r["session_date"],
                    "quality_rating": r["confidence"],
                }
                for r in rows
            ],
            "review_queue": [
                {
                    "id": idx + 1,
                    "takeaway": rv["takeaway"],
                    "duration_min": 30,
                    "session_date": rv["session_date"],
                    "next_review_date": today,
                }
                for idx, rv in enumerate(reviews)
            ],
        }


@app.post("/api/learning/sessions")
def log_session(req: SessionCreateRequest):
    if not req.takeaway or not req.takeaway.strip():
        raise HTTPException(status_code=400, detail="Key takeaway is required")
    with get_conn() as conn:
        # If no items exist, create a generic one for skill
        items = repo.get_all_learning_items(conn)
        item_id = items[0].id if items else repo.create_learning_item(conn, skill="General", resource="Study")

        session_id = repo.create_learning_session(
            conn,
            learning_item_id=item_id,
            session_date=req.session_date or dates.today(),
            duration_min=req.duration_min,
            takeaway=req.takeaway,
            confidence=req.quality_rating or 4,
        )
    return {"id": session_id, "success": True}


@app.get("/api/insights")
def get_insights(days: int = 30):
    today = dates.today()
    start_date = dates.add_days(today, -days)
    with get_conn() as conn:
        streak = stats_svc.get_streak(conn)
        comp_rate = stats_svc.completion_rate(conn, start_date, today)
        avg_rat = stats_svc.average_rating(conn, start_date, today)
        study_df = stats_svc.study_time_by_skill(conn, start_date, today)
        study_by_skill = []
        if not study_df.empty:
            for _, row in study_df.iterrows():
                study_by_skill.append({"skill_name": row["skill"], "total_min": int(row["total_minutes"])})

        return {
            "streak": streak,
            "completion_rate": comp_rate,
            "average_rating": avg_rat,
            "study_by_skill": study_by_skill,
        }


@app.get("/api/daily-update")
def get_daily_update(date: Optional[str] = None):
    rep_date = date or dates.today()
    with get_conn() as conn:
        prefill = daily_svc.get_prefill(conn, rep_date)
        open_tasks = repo.get_todo_tasks_for_date(conn, rep_date)
        existing_update = repo.get_daily_update(conn, rep_date)

        return {
            "report_date": rep_date,
            "prefill": {
                "completed_count": prefill["tasks_completed_count"],
                "planned_count": prefill["tasks_completed_count"] + len(open_tasks),
                "study_minutes": prefill["study_minutes"],
            },
            "open_tasks": [
                {
                    "id": t.id,
                    "title": t.title,
                    "category": t.category,
                    "priority": t.priority,
                    "status": t.status,
                }
                for t in open_tasks
            ],
            "is_closed": existing_update is not None,
            "existing": (
                {
                    "wins": existing_update.wins,
                    "blockers": existing_update.blockers,
                    "focus_tomorrow": existing_update.focus_tomorrow,
                    "mood_rating": existing_update.mood_rating,
                    "productivity_rating": existing_update.productivity_rating,
                }
                if existing_update
                else None
            ),
        }


@app.post("/api/daily-update/close")
def close_daily_update(req: CloseDayRequest):
    with get_conn() as conn:
        daily_svc.close_day(
            conn,
            today_date=req.report_date,
            carry_task_ids=req.carry_task_ids,
            drop_task_ids=req.drop_task_ids,
            wins=req.wins,
            blockers=req.blockers,
            focus_tomorrow=req.focus_tomorrow,
            mood_rating=req.mood_rating,
            productivity_rating=req.productivity_rating,
        )
    return {"success": True}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
