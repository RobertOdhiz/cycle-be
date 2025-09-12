from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field
from uuid import UUID, uuid4
from enum import Enum as PyEnum
from sqlalchemy import Column, Enum as SAEnum

class VerificationStatus(PyEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class VerificationDoc(SQLModel, table=True):
    __tablename__ = "verification_docs"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id")
    cloudinary_url: Optional[str] = None
    status: VerificationStatus = Field(
        default=VerificationStatus.PENDING,
        sa_column=Column(SAEnum(VerificationStatus, native_enum=False), nullable=False),
    )
    submitted_at: datetime = Field(default_factory=datetime.utcnow)
    reviewed_by: Optional[UUID] = Field(default=None, foreign_key="users.id")
    reviewed_at: Optional[datetime] = None
    notes: Optional[str] = None
    
    class Config:
        arbitrary_types_allowed = True
