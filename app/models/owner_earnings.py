from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field
from uuid import UUID, uuid4
from decimal import Decimal
from sqlalchemy import Column, Numeric


class OwnerEarnings(SQLModel, table=True):
    __tablename__ = "owner_earnings"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    owner_id: UUID = Field(foreign_key="users.id")
    rental_id: UUID = Field(foreign_key="rentals.id")
    amount: Decimal = Field(sa_column=Column(Numeric(12, 2)))
    owner_share: Decimal = Field(sa_column=Column(Numeric(8, 4)))
    cycle_share: Decimal = Field(sa_column=Column(Numeric(8, 4)))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        arbitrary_types_allowed = True
