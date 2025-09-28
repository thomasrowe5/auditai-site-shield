from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from app.db.session import Base


class User(Base):
    __tablename__ = "users"

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False)


class Project(Base):
    __tablename__ = "projects"

    project_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    description = Column(Text)
    location = Column(String)
    start_date = Column(DateTime(timezone=True), server_default=func.now())
    end_date = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # nullable=True so you can create projects before wiring real auth
    owner_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="SET NULL"),
        nullable=True
    )

from sqlalchemy import LargeBinary

class SafetyDocument(Base):
    __tablename__ = "safety_documents"

    document_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=False)
    file_name = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    upload_date = Column(DateTime(timezone=True), server_default=func.now())
    notes = Column(Text, nullable=True)
    file_content = Column(LargeBinary)  # for storing raw file bytes (optional)

class Subcontractor(Base):
    __tablename__ = "subcontractors"

    subcontractor_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    trade = Column(String, nullable=True)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    insurance_expiration = Column(DateTime(timezone=True), nullable=True)
    license_expiration = Column(DateTime(timezone=True), nullable=True)
    safety_cert_expiration = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Computed field (not stored): risk status based on expiration dates

from sqlalchemy import Column, String, Date, DateTime, Enum, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

class SubcontractorDocument(Base):
    __tablename__ = "subcontractor_documents"

    doc_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subcontractor_id = Column(UUID(as_uuid=True), ForeignKey("subcontractors.subcontractor_id", ondelete="CASCADE"))
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.project_id", ondelete="CASCADE"))
    file_url = Column(Text, nullable=False)
    doc_type = Column(String, nullable=False)
    issue_date = Column(Date, nullable=True)
    expiration_date = Column(Date, nullable=True)
    verification_status = Column(String, default="pending")
    last_checked = Column(DateTime, default=datetime.utcnow)
# --- AgentOps task log ---
from sqlalchemy import Column, String, Enum, DateTime
from datetime import datetime
import uuid as _uuid

def uuid_str() -> str:
    return str(_uuid.uuid4())

class AgentTask(Base):
    __tablename__ = "agent_tasks"

    task_id = Column(String, primary_key=True, default=uuid_str)
    trigger_type = Column(String, nullable=False)  # e.g., document_verification, bulk_document_verification
    related_id = Column(String, nullable=True)     # doc_id or subcontractor_id
    action_taken = Column(String, nullable=False)  # short human-readable description
    status = Column(String, nullable=False, default="completed")  # completed | failed | pending
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

