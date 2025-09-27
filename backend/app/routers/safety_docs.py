from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Form
from sqlalchemy.orm import Session
from uuid import UUID
from app.db.session import SessionLocal
from app.db import models
from app.schemas import safety_doc as schemas

router = APIRouter(prefix="/safety-docs", tags=["Safety Documents"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=schemas.SafetyDocOut)
async def upload_safety_doc(
    project_id: UUID = Form(...),
    notes: str = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # check if project exists
    project = db.query(models.Project).filter(models.Project.project_id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    content = await file.read()
    new_doc = models.SafetyDocument(
        project_id=project_id,
        file_name=file.filename,
        file_type=file.content_type,
        notes=notes,
        file_content=content
    )
    db.add(new_doc)
    db.commit()
    db.refresh(new_doc)
    return new_doc

@router.get("/project/{project_id}", response_model=list[schemas.SafetyDocOut])
def list_docs_for_project(project_id: UUID, db: Session = Depends(get_db)):
    return db.query(models.SafetyDocument).filter(models.SafetyDocument.project_id == project_id).all()

@router.get("/{document_id}", response_model=schemas.SafetyDocOut)
def get_doc(document_id: UUID, db: Session = Depends(get_db)):
    doc = db.query(models.SafetyDocument).filter(models.SafetyDocument.document_id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc

