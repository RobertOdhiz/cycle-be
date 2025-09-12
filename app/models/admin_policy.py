from datetime import datetime
from typing import Optional, Dict, Any
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, JSON


class AdminPolicy(SQLModel, table=True):
    __tablename__ = "admin_policies"
    
    key: str = Field(primary_key=True)
    value: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        arbitrary_types_allowed = True
