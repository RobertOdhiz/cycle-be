from datetime import datetime
from typing import Optional, Dict, Any
from sqlmodel import SQLModel, Field
from uuid import UUID, uuid4
from sqlalchemy import Column, JSON


class AuditLog(SQLModel, table=True):
    __tablename__ = "audit_logs"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    actor_id: Optional[UUID] = Field(default=None, foreign_key="users.id")
    action: str
    target_type: Optional[str] = None
    target_id: Optional[UUID] = None
    details: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        arbitrary_types_allowed = True
