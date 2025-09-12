# app/models/payment.py
from __future__ import annotations
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import uuid4

from sqlmodel import SQLModel, Field
from sqlalchemy import Column, Enum as SQLEnum, Numeric


class PaymentMethod(str, Enum):
    mpesa = "mpesa"
    card = "card"
    wallet = "wallet"


class PaymentStatus(str, Enum):
    pending = "pending"
    success = "success"
    failed = "failed"


class Payment(SQLModel, table=True):
    __tablename__ = "payments"

    id: Optional[str] = Field(default_factory=lambda: str(uuid4()), primary_key=True, nullable=False)
    rental_id: str = Field(foreign_key="rentals.id", nullable=False)
    user_id: str = Field(foreign_key="users.id", nullable=False)

    # place nullable on the Column when using sa_column
    amount: Decimal = Field(sa_column=Column(Numeric(12, 2), nullable=False))

    method: PaymentMethod = Field(
        sa_column=Column(
            SQLEnum(PaymentMethod, name="paymentmethod_enum"),
            nullable=False
        ),
        default=PaymentMethod.mpesa
    )

    provider_ref: Optional[str] = None

    status: PaymentStatus = Field(
        sa_column=Column(
            SQLEnum(PaymentStatus, name="paymentstatus_enum"),
            nullable=False,
            server_default=PaymentStatus.pending.value
        ),
        default=PaymentStatus.pending
    )

    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
