from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from decimal import Decimal


class PaymentCreateRequest(BaseModel):
    rental_id: UUID
    amount: Decimal = Field(..., decimal_places=2, ge=0)
    payment_method: str = Field(..., pattern="^(mpesa|card|cash|wallet)$")
    phone: Optional[str] = None
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class MpesaSTKRequest(BaseModel):
    rental_id: str
    phone: str = Field(..., pattern="^254[0-9]{9}$")  # Kenyan phone format
    amount: Decimal = Field(..., decimal_places=2, ge=1)
    reference: Optional[str] = None


class MpesaSTKResponse(BaseModel):
    checkout_request_id: str
    merchant_request_id: str
    response_code: str
    response_description: str
    customer_message: str
    expires_at: datetime


class MpesaWebhookData(BaseModel):
    Body: Dict[str, Any]
    Headers: Dict[str, Any]


class PaymentResponse(BaseModel):
    id: UUID
    rental_id: UUID
    user_id: UUID
    amount: Decimal
    payment_method: str
    status: str = Field(..., pattern="^(pending|processing|completed|failed|cancelled)$")
    transaction_id: Optional[str] = None
    phone: Optional[str] = None
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None


class PaymentListResponse(BaseModel):
    payments: List[PaymentResponse]
    total: int


class PaymentStatusUpdateRequest(BaseModel):
    payment_id: UUID
    status: str = Field(..., pattern="^(pending|processing|completed|failed|cancelled)$")
    transaction_id: Optional[str] = None
    failure_reason: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class PaymentRefundRequest(BaseModel):
    payment_id: UUID
    amount: Optional[Decimal] = None  # If None, refunds full amount
    reason: str
    metadata: Optional[Dict[str, Any]] = None


class PaymentRefundResponse(BaseModel):
    refund_id: UUID
    payment_id: UUID
    amount: Decimal
    reason: str
    status: str
    created_at: datetime


class PaymentMethodRequest(BaseModel):
    payment_method: str = Field(..., pattern="^(mpesa|card|cash|wallet)$")
    is_default: bool = False
    metadata: Optional[Dict[str, Any]] = None


class PaymentMethodResponse(BaseModel):
    id: UUID
    user_id: UUID
    payment_method: str
    is_default: bool
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime


class PaymentStatsResponse(BaseModel):
    total_payments: int
    total_amount: Decimal
    successful_payments: int
    failed_payments: int
    pending_payments: int
    average_payment_amount: Decimal
    payment_methods_distribution: Dict[str, int]


class PaymentSearchRequest(BaseModel):
    user_id: Optional[UUID] = None
    rental_id: Optional[UUID] = None
    status: Optional[str] = None
    payment_method: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None
    page: int = 1
    size: int = 20


class PaymentSearchResponse(BaseModel):
    payments: List[PaymentResponse]
    total: int
    page: int
    size: int
    pages: int


class OwnerEarningsRequest(BaseModel):
    user_id: UUID
    start_date: datetime
    end_date: datetime


class OwnerEarningsResponse(BaseModel):
    user_id: UUID
    total_earnings: Decimal
    total_rides: int
    average_per_ride: Decimal
    earnings_by_date: List[Dict[str, Any]]
    pending_payouts: Decimal
