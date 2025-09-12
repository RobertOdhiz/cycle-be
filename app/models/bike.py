# app/models/bike.py
from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import Optional, List
from uuid import UUID, uuid4


from sqlmodel import SQLModel, Field, Column
from sqlalchemy import Enum as SQLEnum, JSON

class BikeType(str, Enum):
    standard = "standard"
    premium = "premium"
    old = "old"

class BikeCondition(str, Enum):
    A = "A"
    B = "B"
    C = "C"

class BikeStatus(str, Enum):
    available = "available"
    rented = "rented"
    maintenance = "maintenance"
    inactive = "inactive"

class Bike(SQLModel, table=True):
    __tablename__ = "bikes"

    id: UUID = Field(default_factory=uuid4, primary_key=True, nullable=False)
    owner_id: Optional[UUID] = Field(default=None, foreign_key="users.id")
    
    type: BikeType = Field(
        sa_column=Column(
            SQLEnum(BikeType, name="biketype_enum"),
            nullable=False,
            server_default=BikeType.standard.value
        ),
        default=BikeType.standard
    )

    condition: BikeCondition = Field(
        sa_column=Column(
            SQLEnum(BikeCondition, name="bikecondition_enum"),
            nullable=False,
            server_default=BikeCondition.B.value
        ),
        default=BikeCondition.B
    )

    hourly_rate: int = Field(default=50, nullable=False)  # enforced min/max by admin policies
    dock_id: Optional[UUID] = Field(default=None, foreign_key="docks.id")

    status: BikeStatus = Field(
        sa_column=Column(
            SQLEnum(BikeStatus, name="bikestatus_enum"),
            nullable=False,
            server_default=BikeStatus.available.value
        ),
        default=BikeStatus.available
    )

    qr_token_hash: Optional[str] = None
    gps_tracker_id: Optional[UUID] = None
    photos: Optional[List] = Field(default=None, sa_column=Column(JSON))

    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    locked: bool = Field(default=False, nullable=False)
    locked_at: Optional[datetime] = None
    unlocked_at: Optional[datetime] = None
    rented_at: Optional[datetime] = None
    returned_at: Optional[datetime] = None
    available_at: Optional[datetime] = None