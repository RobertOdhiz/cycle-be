from typing import Optional, List
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime


class DockCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)
    capacity: int = Field(..., ge=1, le=1000)
    address: Optional[str] = None
    description: Optional[str] = None
    is_active: bool = True


class DockUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    lat: Optional[float] = Field(None, ge=-90, le=90)
    lng: Optional[float] = Field(None, ge=-180, le=180)
    capacity: Optional[int] = Field(None, ge=1, le=1000)
    address: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class DockResponse(BaseModel):
    id: UUID
    name: str
    lat: float
    lng: float
    capacity: int
    available_count: int
    address: Optional[str] = None
    description: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class DockListResponse(BaseModel):
    docks: List[DockResponse]
    total: int


class DockLocationQuery(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)
    radius: float = Field(..., ge=0.1, le=50.0)  # in kilometers
    since: Optional[datetime] = None


class DockNearbyResponse(BaseModel):
    docks: List[DockResponse]
    total: int
    query_center: dict
    radius_km: float


class DockStatsResponse(BaseModel):
    dock_id: UUID
    total_rentals: int
    total_revenue: float
    average_rental_duration: float
    peak_hours: List[int]
    utilization_rate: float


class DockAvailabilityRequest(BaseModel):
    dock_id: UUID
    date: datetime
    time_slot: Optional[str] = None


class DockAvailabilityResponse(BaseModel):
    dock_id: UUID
    date: datetime
    available_slots: List[dict]
    total_capacity: int
    current_usage: int
