from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from decimal import Decimal


class AdminAnalyticsRequest(BaseModel):
    start_date: datetime
    end_date: datetime
    metrics: List[str] = Field(..., min_items=1)  # e.g., ["dau", "revenue", "rides"]
    group_by: Optional[str] = Field(None, pattern="^(day|week|month|quarter|year)$")
    filters: Optional[Dict[str, Any]] = None


class AdminAnalyticsResponse(BaseModel):
    period: Dict[str, Any]
    metrics: Dict[str, Any]
    data_points: List[Dict[str, Any]]
    summary: Dict[str, Any]


class DAUAnalyticsResponse(BaseModel):
    date: str
    dau: int
    mau: int  # Monthly Active Users
    wau: int  # Weekly Active Users
    new_users: int
    returning_users: int
    total_users: int


class RevenueAnalyticsResponse(BaseModel):
    period: str
    total_revenue: Decimal
    total_rides: int
    average_ride_value: Decimal
    revenue_by_payment_method: Dict[str, Decimal]
    revenue_by_zone: Dict[str, Decimal]
    revenue_by_dock: Dict[str, Decimal]


class TripAnalyticsResponse(BaseModel):
    period: str
    total_trips: int
    completed_trips: int
    cancelled_trips: int
    average_duration: float
    average_distance: float
    trips_by_hour: Dict[int, int]
    trips_by_day: Dict[str, int]
    trips_by_zone: Dict[str, int]


class DockAnalyticsResponse(BaseModel):
    dock_id: UUID
    dock_name: str
    total_trips: int
    total_revenue: Decimal
    utilization_rate: float
    peak_hours: List[int]
    average_rental_duration: float
    popular_destinations: List[Dict[str, Any]]


class UserPolicyUpdateRequest(BaseModel):
    user_id: str
    owner_max_bikes: int = Field(..., ge=0, le=100)
    verified_status: Optional[str] = Field(None, pattern="^(unverified|pending|verified|rejected)$")
    eco_points: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None
    admin_notes: Optional[str] = None


class UserPolicyUpdateResponse(BaseModel):
    user_id: str
    owner_max_bikes: int
    verified_status: str
    eco_points: int
    is_active: bool
    admin_notes: Optional[str] = None
    updated_at: datetime
    updated_by: UUID


class UserSearchAdminRequest(BaseModel):
    query: Optional[str] = None
    verified_status: Optional[str] = None
    school: Optional[str] = None
    year: Optional[str] = None
    is_active: Optional[bool] = None
    min_eco_points: Optional[int] = None
    max_eco_points: Optional[int] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    page: int = 1
    size: int = 50


class UserSearchAdminResponse(BaseModel):
    users: List[Dict[str, Any]]
    total: int
    page: int
    size: int
    pages: int
    summary: Dict[str, Any]


class PayoutApprovalRequest(BaseModel):
    payout_id: str
    action: str = Field(..., pattern="^(approve|reject|hold)$")
    notes: Optional[str] = None
    rejection_reason: Optional[str] = None
    hold_reason: Optional[str] = None


class PayoutApprovalResponse(BaseModel):
    payout_id: str
    action: str
    status: str
    notes: Optional[str] = None
    rejection_reason: Optional[str] = None
    hold_reason: Optional[str] = None
    approved_by: UUID
    approved_at: datetime


class PayoutListRequest(BaseModel):
    status: Optional[str] = Field(None, pattern="^(pending|approved|rejected|held|completed)$")
    user_id: Optional[str] = None
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    page: int = 1
    size: int = 50


class PayoutListResponse(BaseModel):
    payouts: List[Dict[str, Any]]
    total: int
    page: int
    size: int
    pages: int
    summary: Dict[str, Any]


class SystemHealthResponse(BaseModel):
    status: str = Field(..., pattern="^(healthy|warning|critical)$")
    database: Dict[str, Any]
    redis: Dict[str, Any]
    external_services: Dict[str, Any]
    last_check: datetime
    uptime: str


class AdminActionLogRequest(BaseModel):
    action: str = Field(..., min_length=1, max_length=100)
    target_type: str = Field(..., pattern="^(user|bike|dock|zone|payment|payout|system)$")
    target_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class AdminActionLogResponse(BaseModel):
    id: UUID
    admin_user_id: UUID
    action: str
    target_type: str
    target_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime


class AdminActionLogSearchRequest(BaseModel):
    admin_user_id: Optional[UUID] = None
    action: Optional[str] = None
    target_type: Optional[str] = None
    target_id: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    page: int = 1
    size: int = 50


class AdminActionLogSearchResponse(BaseModel):
    logs: List[AdminActionLogResponse]
    total: int
    page: int
    size: int
    pages: int


class BulkActionRequest(BaseModel):
    action: str = Field(..., min_length=1, max_length=100)
    target_ids: List[str] = Field(..., min_items=1)
    parameters: Optional[Dict[str, Any]] = None
    dry_run: bool = False


class BulkActionResponse(BaseModel):
    action: str
    total_targets: int
    successful: List[str]
    failed: List[Dict[str, Any]]
    dry_run: bool
    execution_time: float


class AdminDashboardResponse(BaseModel):
    overview: Dict[str, Any]
    recent_activity: List[Dict[str, Any]]
    alerts: List[Dict[str, Any]]
    quick_stats: Dict[str, Any]
    last_updated: datetime
