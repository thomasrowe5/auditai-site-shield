from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional
from uuid import UUID

class SubcontractorBase(BaseModel):
    project_id: UUID
    name: str
    trade: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    insurance_expiration: Optional[datetime] = None
    license_expiration: Optional[datetime] = None
    safety_cert_expiration: Optional[datetime] = None

class SubcontractorCreate(SubcontractorBase):
    pass

class SubcontractorUpdate(SubcontractorBase):
    project_id: Optional[UUID] = None
    name: Optional[str] = None

class SubcontractorOut(SubcontractorBase):
    subcontractor_id: UUID
    created_at: datetime
    risk_status: str

    class Config:
        from_attributes = True

