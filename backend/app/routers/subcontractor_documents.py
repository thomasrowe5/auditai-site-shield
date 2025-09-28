from __future__ import annotations

import os
import uuid
import shutil
from uuid import UUID
from datetime import datetime, date
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db import models, session

router = APIRouter(prefix="/subcontractors", tags=["Subcontractor Documents"])

# ---- Resolve absolute /uploads dir (backend/uploads) ----
# This file is app/routers/subcontractor_documents.py
# Go up 3 levels to reach backend/, then /uploads
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)


# ---------------- Utilities ----------------
def _compute_status(expiration: Optional[date]) -> str:
    if not expiration:
        return "unknown"
    today = datetime.utcnow().date()
    delta = (expiration - today).days
    if delta < 0:
        return "expired"
    if delta <= 30:
        return "expiring_soon"
    return "valid"


def update_subcontractor_risk_status(subcontractor_id: str, db: Session) -> None:
    """Derive subcontractor.risk_status from all its document statuses."""
    docs = (
        db.query(models.SubcontractorDocument)
        .filter(models.SubcontractorDocument.subcontractor_id == subcontractor_id)
        .all()
    )
    if not docs:
        return

    has_expired = any(d.verification_status == "expired" for d in docs)
    has_soon = any(d.verification_status == "expiring_soon" for d in docs)

    sub = (
        db.query(models.Subcontractor)
        .filter(models.Subcontractor.subcontractor_id == subcontractor_id)
        .first()
    )
    if not sub:
        return

    if has_expired:
        sub.risk_status = "❌ Non-Compliant"
    elif has_soon:
        sub.risk_status = "⚠️ Expiring Soon"
    else:
        sub.risk_status = "✅ Compliant"


def log_agent_task(
    db: Session,
    trigger_type: str,
    related_id: str,
    action_taken: str,
    status: str = "completed",
) -> None:
    """Append a row to agent_tasks (no commit here; caller controls tx)."""
    task = models.AgentTask(
        task_id=str(uuid.uuid4()),
        trigger_type=trigger_type,
        related_id=related_id,
        action_taken=action_taken,
        status=status,
        created_at=datetime.utcnow(),
    )
    db.add(task)


# --------------- Schemas -------------------
class VerifyPayload(BaseModel):
    issue_date: Optional[date] = None
    expiration_date: Optional[date] = None


# --------------- Endpoints -----------------

@router.post("/{subcontractor_id}/documents/", summary="Upload a subcontractor document")
def upload_subcontractor_document(
    subcontractor_id: UUID,
    doc_type: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(session.get_db),
):
    subcontractor_id = str(subcontractor_id)

    sub = (
        db.query(models.Subcontractor)
        .filter(models.Subcontractor.subcontractor_id == subcontractor_id)
        .first()
    )
    if not sub:
        raise HTTPException(status_code=404, detail="Subcontractor not found")

    doc_id = str(uuid.uuid4())
    safe_name = file.filename or "upload.bin"
    file_name = f"{doc_id}_{safe_name}"

    # Save to absolute path; store relative "uploads/..." in DB
    abs_path = os.path.join(UPLOADS_DIR, file_name)
    rel_path = f"uploads/{file_name}"
    with open(abs_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    new_doc = models.SubcontractorDocument(
        doc_id=doc_id,
        subcontractor_id=subcontractor_id,
        project_id=sub.project_id,
        file_url=rel_path,
        doc_type=doc_type,
        issue_date=None,
        expiration_date=None,
        verification_status="pending",
        last_checked=datetime.utcnow(),
    )
    db.add(new_doc)
    db.commit()
    db.refresh(new_doc)
    return new_doc


@router.get("/{subcontractor_id}/documents/", summary="List subcontractor documents")
def list_subcontractor_documents(
    subcontractor_id: UUID, db: Session = Depends(session.get_db)
):
    subcontractor_id = str(subcontractor_id)
    docs = (
        db.query(models.SubcontractorDocument)
        .filter(models.SubcontractorDocument.subcontractor_id == subcontractor_id)
        .all()
    )
    return docs


@router.delete("/documents/{doc_id}", summary="Delete a subcontractor document")
def delete_subcontractor_document(doc_id: UUID, db: Session = Depends(session.get_db)):
    doc_id = str(doc_id)

    doc = (
        db.query(models.SubcontractorDocument)
        .filter(models.SubcontractorDocument.doc_id == doc_id)
        .first()
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Try removing file; ignore failures
    try:
        abs_path = (
            os.path.join(BASE_DIR, doc.file_url)
            if not os.path.isabs(doc.file_url)
            else doc.file_url
        )
        if os.path.exists(abs_path):
            os.remove(abs_path)
    except Exception:
        pass

    sub_id = doc.subcontractor_id
    db.delete(doc)
    update_subcontractor_risk_status(sub_id, db)
    db.commit()
    return {"detail": "Document deleted successfully"}


@router.post("/documents/{doc_id}/verify", summary="Set dates (optional) and verify one document")
def verify_document(
    doc_id: UUID,
    payload: Optional[VerifyPayload] = None,
    db: Session = Depends(session.get_db),
):
    doc_id = str(doc_id)

    doc = (
        db.query(models.SubcontractorDocument)
        .filter(models.SubcontractorDocument.doc_id == doc_id)
        .first()
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Apply changes from payload if supplied
    if payload:
        if payload.issue_date is not None:
            doc.issue_date = payload.issue_date
        if payload.expiration_date is not None:
            doc.expiration_date = payload.expiration_date

    doc.verification_status = _compute_status(doc.expiration_date)
    doc.last_checked = datetime.utcnow()

    # Log task + update sub risk (single transaction)
    log_agent_task(db, "document_verification", doc_id, f"Status -> {doc.verification_status}")
    update_subcontractor_risk_status(doc.subcontractor_id, db)

    db.commit()
    db.refresh(doc)

    days_until = (
        (doc.expiration_date - datetime.utcnow().date()).days
        if doc.expiration_date
        else None
    )
    return {
        "doc_id": str(doc.doc_id),
        "subcontractor_id": str(doc.subcontractor_id),
        "project_id": str(doc.project_id),
        "doc_type": doc.doc_type,
        "issue_date": doc.issue_date,
        "expiration_date": doc.expiration_date,
        "verification_status": doc.verification_status,
        "days_until_expiration": days_until,
        "last_checked": doc.last_checked,
        "file_url": doc.file_url,
    }


@router.post("/{subcontractor_id}/documents/verify", summary="Verify all documents for a subcontractor")
def verify_all_documents_for_subcontractor(
    subcontractor_id: UUID, db: Session = Depends(session.get_db)
):
    subcontractor_id = str(subcontractor_id)

    docs = (
        db.query(models.SubcontractorDocument)
        .filter(models.SubcontractorDocument.subcontractor_id == subcontractor_id)
        .all()
    )
    if not docs:
        raise HTTPException(
            status_code=404, detail="No documents found for subcontractor"
        )

    today = datetime.utcnow().date()
    result: List[Dict[str, Any]] = []
    for d in docs:
        d.verification_status = _compute_status(d.expiration_date)
        d.last_checked = datetime.utcnow()
        days_until = (d.expiration_date - today).days if d.expiration_date else None
        result.append(
            {
                "doc_id": str(d.doc_id),
                "doc_type": d.doc_type,
                "issue_date": d.issue_date,
                "expiration_date": d.expiration_date,
                "verification_status": d.verification_status,
                "days_until_expiration": days_until,
                "file_url": d.file_url,
                "last_checked": d.last_checked,
            }
        )

    log_agent_task(
        db,
        "bulk_document_verification",
        subcontractor_id,
        f"Updated {len(result)} documents",
    )
    update_subcontractor_risk_status(subcontractor_id, db)

    db.commit()

    return {
        "subcontractor_id": subcontractor_id,
        "updated": len(result),
        "documents": result,
    }

