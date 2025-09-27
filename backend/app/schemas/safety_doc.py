from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from uuid import UUID

class SafetyDocBase(BaseModel):
    project_id: UUID
    notes: Optional[str] = None

class SafetyDocCreate(SafetyDocBase):
    pass

class SafetyDocOut(SafetyDocBase):
    document_id: UUID
    file_name: str
    file_type: str
    upload_date: datetime

    class Config:
        from_attributes = True

