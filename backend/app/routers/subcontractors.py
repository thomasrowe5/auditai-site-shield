from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime
from app.db.session import SessionLocal
from app.db import models
from app.schemas import subcontractor as schemas

router = APIRouter(prefix="/subcontractors", tags=["Subcontractors"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def calculate_risk(sub):
    today = datetime.utcnow()
    expiring_fields = []
    if sub.insurance_expiration and sub.insurance_expiration < today:
        expiring_fields.append("Insurance expired")
    if sub.license_expiration and sub.license_expiration < today:
        expiring_fields.append("License expired")
    if sub.safety_cert_expiration and sub.safety_cert_expiration < today:
        expiring_fields.append("Safety cert expired")

    if expiring_fields:
        return "❌ Non-compliant: " + ", ".join(expiring_fields)
    return "✅ Compliant"

@router.post("/", response_model=schemas.SubcontractorOut)
def create_subcontractor(data: schemas.SubcontractorCreate, db: Session = Depends(get_db)):
    sub = models.Subcontractor(**data.model_dump())
    db.add(sub)
    db.commit()
    db.refresh(sub)
    return schemas.SubcontractorOut(**sub.__dict__, risk_status=calculate_risk(sub))

@router.get("/project/{project_id}", response_model=list[schemas.SubcontractorOut])
def list_subcontractors(project_id: UUID, db: Session = Depends(get_db)):
    subs = db.query(models.Subcontractor).filter(models.Subcontractor.project_id == project_id).all()
    return [schemas.SubcontractorOut(**s.__dict__, risk_status=calculate_risk(s)) for s in subs]

@router.get("/{subcontractor_id}", response_model=schemas.SubcontractorOut)
def get_subcontractor(subcontractor_id: UUID, db: Session = Depends(get_db)):
    sub = db.query(models.Subcontractor).filter(models.Subcontractor.subcontractor_id == subcontractor_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Subcontractor not found")
    return schemas.SubcontractorOut(**sub.__dict__, risk_status=calculate_risk(sub))

@router.patch("/{subcontractor_id}", response_model=schemas.SubcontractorOut)
def update_subcontractor(subcontractor_id: UUID, update: schemas.SubcontractorUpdate, db: Session = Depends(get_db)):
    sub = db.query(models.Subcontractor).filter(models.Subcontractor.subcontractor_id == subcontractor_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Subcontractor not found")

    for key, value in update.model_dump(exclude_unset=True).items():
        setattr(sub, key, value)

    db.commit()
    db.refresh(sub)
    return schemas.SubcontractorOut(**sub.__dict__, risk_status=calculate_risk(sub))

@router.delete("/{subcontractor_id}")
def delete_subcontractor(subcontractor_id: UUID, db: Session = Depends(get_db)):
    sub = db.query(models.Subcontractor).filter(models.Subcontractor.subcontractor_id == subcontractor_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Subcontractor not found")
    db.delete(sub)
    db.commit()
    return {"detail": "Subcontractor deleted successfully"}

