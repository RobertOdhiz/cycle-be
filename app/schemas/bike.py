from typing import Optional, List
from pydantic import BaseModel, Field
from uuid import UUID
from decimal import Decimal


class BikeCreateRequest(BaseModel):
    type: str = Field(..., pattern="^(standard|premium|old)$")
    condition: str = Field(..., pattern="^(A|B|C)$")
    hourly_rate: int = Field(..., ge=50, le=70)
    dock_id: Optional[UUID] = None
    photos: Optional[List[str]] = None


class BikeUpdateRequest(BaseModel):
    type: Optional[str] = Field(None, pattern="^(standard|premium|old)$")
    condition: Optional[str] = Field(None, pattern="^(A|B|C)$")
    hourly_rate: Optional[int] = Field(None, ge=50, le=70)
    dock_id: Optional[UUID] = None
    status: Optional[str] = Field(None, pattern="^(available|rented|maintenance|inactive)$")
    photos: Optional[List[str]] = None


class BikeResponse(BaseModel):
    id: UUID
    owner_id: Optional[UUID] = None
    type: str
    condition: str
    hourly_rate: int
    dock_id: Optional[UUID] = None
    status: str
    photos: Optional[List[str]] = None
    created_at: str
    updated_at: str


class BikeListResponse(BaseModel):
    bikes: List[BikeResponse]


class BatchPricingRequest(BaseModel):
    filter: dict
    hourly_rate: int = Field(..., ge=50, le=70)
