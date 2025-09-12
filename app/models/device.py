from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field
from uuid import UUID, uuid4


class Device(SQLModel, table=True):
    __tablename__ = "devices"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id")
    expo_push_token: Optional[str] = None
    platform: Optional[str] = None
    last_seen: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        arbitrary_types_allowed = True
