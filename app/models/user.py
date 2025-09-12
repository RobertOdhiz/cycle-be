from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import uuid4

from sqlmodel import SQLModel, Field, Column
from sqlalchemy import Enum as SQLEnum, String

class VerificationStatus(str, Enum):
    unverified = "unverified"
    pending = "pending"
    verified = "verified"
    rejected = "rejected"

class User(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[str] = Field(default_factory=lambda: str(uuid4()), primary_key=True, nullable=False)
    email: str = Field(index=True, nullable=False)
    email_verified: bool = Field(default=False, nullable=False)
    password_hash: str = Field(nullable=False)
    name: Optional[str] = None
    phone: Optional[str] = None
    school: Optional[str] = None
    year: Optional[str] = None

    # Use a DB enum for verified_status (mapped from Python Enum)
    verified_status: VerificationStatus = Field(
        sa_column=Column(
            SQLEnum(VerificationStatus, name="verificationstatus_enum"),
            nullable=False,
            server_default=VerificationStatus.unverified.value
        ),
        default=VerificationStatus.unverified
    )

    eco_points: int = Field(default=0, nullable=False)
    owner_max_bikes: int = Field(default=1, nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
