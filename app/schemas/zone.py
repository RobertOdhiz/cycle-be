from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime


class ZoneCreateRequest(BaseModel):
    kind: str = Field(..., pattern="^(restricted|premium|discount|parking|service)$")
    polygon_coords: List[List[List[float]]] = Field(..., min_items=1)  # GeoJSON Polygon coordinates
    label: Optional[str] = None
    description: Optional[str] = None
    rules: Optional[Dict[str, Any]] = None
    is_active: bool = True


class ZoneUpdateRequest(BaseModel):
    kind: Optional[str] = Field(None, pattern="^(restricted|premium|discount|parking|service)$")
    polygon_coords: Optional[List[List[List[float]]]] = None
    label: Optional[str] = None
    description: Optional[str] = None
    rules: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class ZoneResponse(BaseModel):
    id: UUID
    kind: str
    polygon: Dict[str, Any]  # GeoJSON Polygon object
    label: Optional[str] = None
    description: Optional[str] = None
    rules: Optional[Dict[str, Any]] = None
    is_active: bool
    created_by: UUID
    created_at: datetime
    updated_at: datetime


class ZoneListResponse(BaseModel):
    zones: List[ZoneResponse]
    total: int


class ZoneQueryRequest(BaseModel):
    kind: Optional[str] = None
    is_active: Optional[bool] = None
    lat: Optional[float] = Field(None, ge=-90, le=90)
    lng: Optional[float] = Field(None, ge=-180, le=180)
    page: int = 1
    size: int = 20


class ZoneQueryResponse(BaseModel):
    zones: List[ZoneResponse]
    total: int
    page: int
    size: int
    pages: int


class ZoneStatsResponse(BaseModel):
    zone_id: UUID
    total_rentals: int
    total_revenue: float
    average_rental_duration: float
    peak_usage_hours: List[int]
    popular_docks: List[UUID]


class ZoneRulesRequest(BaseModel):
    zone_id: UUID
    rules: Dict[str, Any]


class ZoneRulesResponse(BaseModel):
    zone_id: UUID
    rules: Dict[str, Any]
    updated_at: datetime


class ZoneOverlapRequest(BaseModel):
    polygon_coords: List[List[List[float]]] = Field(..., min_items=1)
    exclude_zone_id: Optional[UUID] = None


class ZoneOverlapResponse(BaseModel):
    has_overlap: bool
    overlapping_zones: List[ZoneResponse]
    overlap_area: Optional[float] = None


class ZoneBulkCreateRequest(BaseModel):
    zones: List[ZoneCreateRequest]


class ZoneBulkCreateResponse(BaseModel):
    created_zones: List[ZoneResponse]
    failed_zones: List[Dict[str, Any]]
    total_created: int
    total_failed: int
