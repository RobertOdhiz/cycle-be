from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime


class NotificationCreateRequest(BaseModel):
    user_ids: List[str] = Field(..., min_items=1)
    channel: str = Field(..., pattern="^(push|email|sms|in_app)$")
    title: str = Field(..., min_length=1, max_length=100)
    body: str = Field(..., min_length=1, max_length=500)
    data: Optional[Dict[str, Any]] = None
    priority: str = Field(default="normal", pattern="^(low|normal|high|urgent)$")
    scheduled_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None


class NotificationSendRequest(BaseModel):
    user_ids: List[str] = Field(..., min_items=1)
    channel: str = Field(..., pattern="^(push|email|sms|in_app)$")
    title: str = Field(..., min_length=1, max_length=100)
    body: str = Field(..., min_length=1, max_length=500)
    data: Optional[Dict[str, Any]] = None
    priority: str = Field(default="normal", pattern="^(low|normal|high|urgent)$")
    background_tasks: bool = True


class NotificationResponse(BaseModel):
    id: UUID
    user_id: str
    channel: str
    title: str
    body: str
    data: Optional[Dict[str, Any]] = None
    priority: str
    status: str = Field(..., pattern="^(pending|sent|delivered|failed|read)$")
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class NotificationListResponse(BaseModel):
    notifications: List[NotificationResponse]
    total: int
    unread_count: int


class NotificationUpdateRequest(BaseModel):
    notification_id: UUID
    status: Optional[str] = Field(None, pattern="^(pending|sent|delivered|failed|read)$")
    read_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


class NotificationPreferencesRequest(BaseModel):
    push_enabled: bool = True
    email_enabled: bool = True
    sms_enabled: bool = False
    in_app_enabled: bool = True
    marketing_enabled: bool = False
    ride_reminders: bool = True
    payment_notifications: bool = True
    safety_alerts: bool = True
    quiet_hours_start: Optional[str] = None  # Format: "HH:MM"
    quiet_hours_end: Optional[str] = None    # Format: "HH:MM"


class NotificationPreferencesResponse(BaseModel):
    user_id: UUID
    push_enabled: bool
    email_enabled: bool
    sms_enabled: bool
    in_app_enabled: bool
    marketing_enabled: bool
    ride_reminders: bool
    payment_notifications: bool
    safety_alerts: bool
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None
    updated_at: datetime


class NotificationTemplateRequest(BaseModel):
    template_name: str = Field(..., min_length=1, max_length=50)
    title: str = Field(..., min_length=1, max_length=100)
    body: str = Field(..., min_length=1, max_length=500)
    variables: List[str] = Field(default=[])  # Template variables like {user_name}, {ride_id}
    channels: List[str] = Field(..., min_items=1)
    is_active: bool = True


class NotificationTemplateResponse(BaseModel):
    id: UUID
    template_name: str
    title: str
    body: str
    variables: List[str]
    channels: List[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime


class NotificationStatsResponse(BaseModel):
    total_notifications: int
    sent_notifications: int
    delivered_notifications: int
    failed_notifications: int
    read_notifications: int
    delivery_rate: float
    read_rate: float
    notifications_by_channel: Dict[str, int]
    notifications_by_priority: Dict[str, int]


class NotificationSearchRequest(BaseModel):
    user_id: Optional[str] = None
    channel: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    unread_only: bool = False
    page: int = 1
    size: int = 20


class NotificationSearchResponse(BaseModel):
    notifications: List[NotificationResponse]
    total: int
    page: int
    size: int
    pages: int
    unread_count: int


class BulkNotificationRequest(BaseModel):
    notifications: List[NotificationCreateRequest]


class BulkNotificationResponse(BaseModel):
    successful: List[NotificationResponse]
    failed: List[Dict[str, Any]]
    total_sent: int
    total_failed: int


class NotificationWebhookRequest(BaseModel):
    notification_id: UUID
    status: str
    delivery_data: Optional[Dict[str, Any]] = None
    timestamp: datetime
