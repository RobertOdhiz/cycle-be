from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime


class VerificationDocSubmitRequest(BaseModel):
    user_id: str
    s3_url: str = Field(..., min_length=1)
    document_type: str = Field(..., pattern="^(id_card|passport|drivers_license|student_id|other)$")
    document_number: Optional[str] = None
    expiry_date: Optional[datetime] = None
    additional_info: Optional[Dict[str, Any]] = None


class VerificationDocResponse(BaseModel):
    id: UUID
    user_id: str
    s3_url: str
    document_type: str
    document_number: Optional[str] = None
    expiry_date: Optional[datetime] = None
    status: str = Field(..., pattern="^(pending|approved|rejected|expired)$")
    additional_info: Optional[Dict[str, Any]] = None
    reviewed_by: Optional[UUID] = None
    reviewed_at: Optional[datetime] = None
    notes: Optional[str] = None
    rejection_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class VerificationDocUpdateRequest(BaseModel):
    verification_id: UUID
    status: str = Field(..., pattern="^(pending|approved|rejected|expired)$")
    notes: Optional[str] = None
    rejection_reason: Optional[str] = None
    additional_info: Optional[Dict[str, Any]] = None


class VerificationDocListResponse(BaseModel):
    documents: List[VerificationDocResponse]
    total: int
    pending_count: int
    approved_count: int
    rejected_count: int


class VerificationStatusRequest(BaseModel):
    user_id: str
    status: str = Field(..., pattern="^(unverified|pending|verified|rejected)$")
    notes: Optional[str] = None
    admin_notes: Optional[str] = None


class VerificationStatusResponse(BaseModel):
    user_id: str
    status: str
    verified_at: Optional[datetime] = None
    notes: Optional[str] = None
    admin_notes: Optional[str] = None
    updated_at: datetime


class VerificationNudgeRequest(BaseModel):
    user_id: str
    nudge_type: str = Field(..., pattern="^(email|sms|push|in_app)$")
    message: Optional[str] = None
    scheduled_at: Optional[datetime] = None


class VerificationNudgeResponse(BaseModel):
    nudge_id: UUID
    user_id: str
    nudge_type: str
    message: Optional[str] = None
    status: str = Field(..., pattern="^(pending|sent|delivered|failed)$")
    scheduled_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    created_at: datetime


class VerificationReviewRequest(BaseModel):
    verification_id: UUID
    action: str = Field(..., pattern="^(approve|reject|request_changes)$")
    notes: Optional[str] = None
    rejection_reason: Optional[str] = None
    changes_requested: Optional[List[str]] = None


class VerificationReviewResponse(BaseModel):
    verification_id: UUID
    action: str
    status: str
    notes: Optional[str] = None
    rejection_reason: Optional[str] = None
    changes_requested: Optional[List[str]] = None
    reviewed_by: UUID
    reviewed_at: datetime


class VerificationStatsResponse(BaseModel):
    total_submissions: int
    pending_reviews: int
    approved_count: int
    rejected_count: int
    average_review_time: float  # in hours
    submissions_by_type: Dict[str, int]
    submissions_by_status: Dict[str, int]


class VerificationSearchRequest(BaseModel):
    user_id: Optional[str] = None
    document_type: Optional[str] = None
    status: Optional[str] = None
    reviewed_by: Optional[UUID] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    pending_only: bool = False
    page: int = 1
    size: int = 20


class VerificationSearchResponse(BaseModel):
    documents: List[VerificationDocResponse]
    total: int
    page: int
    size: int
    pages: int
    pending_count: int


class VerificationBulkActionRequest(BaseModel):
    verification_ids: List[UUID] = Field(..., min_items=1)
    action: str = Field(..., pattern="^(approve|reject|request_changes)$")
    notes: Optional[str] = None
    rejection_reason: Optional[str] = None


class VerificationBulkActionResponse(BaseModel):
    successful: List[UUID]
    failed: List[Dict[str, Any]]
    total_processed: int
    total_successful: int
    total_failed: int


class VerificationTemplateRequest(BaseModel):
    template_name: str = Field(..., min_length=1, max_length=50)
    subject: str = Field(..., min_length=1, max_length=100)
    body: str = Field(..., min_length=1, max_length=1000)
    variables: List[str] = Field(default=[])
    is_active: bool = True


class VerificationTemplateResponse(BaseModel):
    id: UUID
    template_name: str
    subject: str
    body: str
    variables: List[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime


class VerificationWebhookRequest(BaseModel):
    verification_id: UUID
    status: str
    metadata: Optional[Dict[str, Any]] = None
    timestamp: datetime
