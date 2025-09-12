from datetime import datetime
from typing import Optional, List
from sqlmodel import SQLModel, Field
from uuid import UUID, uuid4
from decimal import Decimal
from enum import Enum as PyEnum
from sqlalchemy import Column, JSON, Numeric, Enum as SAEnum

class RentalStatus(PyEnum):
    OPEN = "open"
    END_PENDING = "end_pending"
    CLOSED = "closed"

class Rental(SQLModel, table=True):
    __tablename__ = "rentals"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    client_rental_id: Optional[str] = None
    bike_id: UUID = Field(foreign_key="bikes.id")
    user_id: UUID = Field(foreign_key="users.id")
    start_at: datetime
    end_at: Optional[datetime] = None
    minute_rate_snapshot: Decimal = Field(sa_column=Column(Numeric(8, 4)))
    minutes_client: Optional[int] = None
    amount: Optional[Decimal] = Field(default=None, sa_column=Column(Numeric(12, 2)))
    status: RentalStatus = Field(
        default=RentalStatus.OPEN,
        sa_column=Column(SAEnum(RentalStatus, native_enum=False), nullable=False),
    )
    path_sample: Optional[List[dict]] = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        arbitrary_types_allowed = True
