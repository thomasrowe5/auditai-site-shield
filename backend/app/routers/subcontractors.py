from __future__ import annotations

from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.db import models, session

router = APIRouter(prefix="/subcontractors", tags=["Subcontractors"])

# ---------- Pydantic (minimal for create/update) ----------
class SubcontractorCreate(BaseModel):
    project_id: str
    name: str
    trade: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    status: Optional[str] = "active"

class SubcontractorUpdate(BaseModel):
    name: Optional[str] = None
    trade: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    status: Optional[str] = None

# ---------- Endpoints ----------
@router.post("/", summary="Create subcontractor")
def create_subcontractor(payload: SubcontractorCreate, db: Session = Depends(session.get_db)):
    new_sub = models.Subcontractor(
        subcontractor_id=models.uuid_str(),  # helper in your models, or use str(uuid4())
        project_id=payload.project_id,
        name=payload.name,
        trade=payload.trade,
        email=payload.email,
        phone=payload.phone,
        status=payload.status or "active",
        risk_status="✅ Compliant",
        created_at=datetime.utcnow(),
    )
    db.add(new_sub)
    db.commit()
    db.refresh(new_sub)
    return new_sub

@router.get("", summary="List subcontractors for a project")
@router.get("/", summary="List subcontractors for a project")
def list_subcontractors(project_id: str, db: Session = Depends(session.get_db)):
    return (
        db.query(models.Subcontractor)
        .filter(models.Subcontractor.project_id == project_id)
        .all()
    )

@router.get("/{subcontractor_id}", summary="Get a subcontractor by id")
def get_subcontractor(subcontractor_id: str, db: Session = Depends(session.get_db)):
    sub = (
        db.query(models.Subcontractor)
        .filter(models.Subcontractor.subcontractor_id == subcontractor_id)
        .first()
    )
    if not sub:
        raise HTTPException(status_code=404, detail="Subcontractor not found")
    return sub

@router.patch("/{subcontractor_id}", summary="Update subcontractor")
def update_subcontractor(subcontractor_id: str, payload: SubcontractorUpdate, db: Session = Depends(session.get_db)):
    sub = (
        db.query(models.Subcontractor)
        .filter(models.Subcontractor.subcontractor_id == subcontractor_id)
        .first()
    )
    if not sub:
        raise HTTPException(status_code=404, detail="Subcontractor not found")

    if payload.name is not None: sub.name = payload.name
    if payload.trade is not None: sub.trade = payload.trade
    if payload.email is not None: sub.email = payload.email
    if payload.phone is not None: sub.phone = payload.phone
    if payload.status is not None: sub.status = payload.status

    db.commit()
    db.refresh(sub)
    return sub

@router.delete("/{subcontractor_id}", summary="Delete subcontractor")
def delete_subcontractor(subcontractor_id: str, db: Session = Depends(session.get_db)):
    sub = (
        db.query(models.Subcontractor)
        .filter(models.Subcontractor.subcontractor_id == subcontractor_id)
        .first()
    )
    if not sub:
        raise HTTPException(status_code=404, detail="Subcontractor not found")

    db.delete(sub)
    db.commit()
    return {"detail": "Subcontractor deleted"}

