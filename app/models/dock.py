from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field
from uuid import UUID, uuid4
from sqlalchemy import Column, Integer
from geoalchemy2 import Geometry


class Dock(SQLModel, table=True):
    __tablename__ = "docks"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str
    geom: bytes = Field(sa_column=Column(Geometry('POINT', srid=4326)))
    capacity: int = Field(default=10)
    available_count: int = Field(default=0)
    address: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        arbitrary_types_allowed = True
