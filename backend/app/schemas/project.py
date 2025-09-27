from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from uuid import UUID


class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None
    location: Optional[str] = None
    end_date: Optional[datetime] = None


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(ProjectBase):
    # when updating, all fields are optional; exclude_unset will handle it
    name: Optional[str] = None


class ProjectOut(ProjectBase):
    project_id: UUID
    owner_id: Optional[UUID] = None
    start_date: datetime
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

