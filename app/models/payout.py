from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field
from uuid import UUID, uuid4
from decimal import Decimal
from enum import Enum
from sqlalchemy import Column, Numeric, Enum as SQLEnum


class PayoutStatus(str, Enum):
    requested = "requested"
    approved = "approved"
    paid = "paid"
    failed = "failed"


class Payout(SQLModel, table=True):
    __tablename__ = "payouts"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    owner_id: UUID = Field(foreign_key="users.id", nullable=False, index=True)
    amount: Decimal = Field(sa_column=Column(Numeric(12, 2), nullable=False))
    status: PayoutStatus = Field(
        default=PayoutStatus.requested,
        sa_column=Column(
            SQLEnum(PayoutStatus, name="payoutstatus_enum"),
            nullable=False,
            server_default=PayoutStatus.requested.value,
            index=True,  # moved index into Column
        ),
    )
    requested_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    processed_at: Optional[datetime] = None
    notes: Optional[str] = None

    class Config:
        arbitrary_types_allowed = True
