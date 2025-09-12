from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field
from uuid import UUID, uuid4
from enum import Enum as PyEnum
from sqlalchemy import Column, Enum as SAEnum
from geoalchemy2 import Geometry


class ZoneKind(PyEnum):
    GREEN = "green"
    RED = "red"


class Zone(SQLModel, table=True):
    __tablename__ = "zones"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    kind: ZoneKind = Field(
        default=ZoneKind.GREEN,
        sa_column=Column(SAEnum(ZoneKind, native_enum=False), nullable=False),
    )
    polygon: bytes = Field(sa_column=Column(Geometry("POLYGON", srid=4326)))
    label: Optional[str] = None
    version: int = Field(default=1)
    created_by: Optional[UUID] = Field(default=None, foreign_key="users.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        arbitrary_types_allowed = True
