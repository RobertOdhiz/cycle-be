from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from uuid import UUID
from decimal import Decimal
from datetime import datetime


class RideStartRequest(BaseModel):
    client_rental_id: Optional[str] = None
    bike_id: UUID
    user_id: UUID
    start_at: datetime
    minute_rate_snapshot: Decimal = Field(..., decimal_places=4)


class RideStartResponse(BaseModel):
    rental_id: UUID
    server_start_at: datetime


class RideEndRequest(BaseModel):
    client_rental_id: Optional[str] = None
    rental_id: Optional[UUID] = None
    end_at: datetime
    minutes_client: int
    end_dock_id: Optional[UUID] = None
    path_sample: Optional[List[Dict[str, Any]]] = None


class RideEndResponse(BaseModel):
    rental_id: UUID
    amount: Decimal
    minutes: int
    payment_instructions: str


class RentalResponse(BaseModel):
    id: UUID
    client_rental_id: Optional[str] = None
    bike_id: UUID
    user_id: UUID
    start_at: datetime
    end_at: Optional[datetime] = None
    minute_rate_snapshot: Decimal
    minutes_client: Optional[int] = None
    amount: Optional[Decimal] = None
    status: str
    path_sample: Optional[List[Dict[str, Any]]] = None
    created_at: datetime
    updated_at: datetime


class RentalListResponse(BaseModel):
    rentals: List[RentalResponse]
