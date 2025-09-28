from __future__ import annotations
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db import models, session

router = APIRouter(prefix="/agent-tasks", tags=["AgentOps"])

@router.get("/", summary="List AgentOps task logs")
def list_agent_tasks(db: Session = Depends(session.get_db)):
    return db.query(models.AgentTask).order_by(models.AgentTask.created_at.desc()).limit(200).all()

@router.get("/{task_id}", summary="Get one AgentOps task")
def get_agent_task(task_id: str, db: Session = Depends(session.get_db)):
    return db.query(models.AgentTask).filter(models.AgentTask.task_id == task_id).first()

