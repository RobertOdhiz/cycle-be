from datetime import datetime
from typing import Optional, Dict, Any
from sqlmodel import SQLModel, Field
from uuid import UUID, uuid4
from sqlalchemy import Column, JSON


class Event(SQLModel, table=True):
    __tablename__ = "events"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: Optional[UUID] = Field(default=None, foreign_key="users.id")
    bike_id: Optional[UUID] = Field(default=None, foreign_key="bikes.id")
    dock_id: Optional[UUID] = Field(default=None, foreign_key="docks.id")
    event_type: str
    properties: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    occurred_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        arbitrary_types_allowed = True
