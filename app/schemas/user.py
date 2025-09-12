from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field
from uuid import UUID
from datetime import datetime


class UserCreateRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    name: str
    phone: Optional[str] = None
    school: Optional[str] = None
    year: Optional[str] = None


class UserUpdateRequest(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    school: Optional[str] = None
    year: Optional[str] = None
    profile_picture: Optional[str] = None


class UserProfileUpdateRequest(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    school: Optional[str] = None
    year: Optional[str] = None
    profile_picture: Optional[str] = None


class UserResponse(BaseModel):
    id: UUID
    email: str
    name: Optional[str] = None
    phone: Optional[str] = None
    school: Optional[str] = None
    year: Optional[str] = None
    profile_picture: Optional[str] = None
    email_verified: bool
    verified_status: str
    eco_points: int
    owner_max_bikes: int
    created_at: datetime
    updated_at: datetime


class UserListResponse(BaseModel):
    users: List[UserResponse]
    total: int


class UserStatsResponse(BaseModel):
    total_rides: int
    total_distance: float
    total_eco_points: int
    favorite_docks: List[str]
    average_ride_duration: float


class UserPreferencesRequest(BaseModel):
    notification_preferences: Optional[dict] = None
    privacy_settings: Optional[dict] = None
    language: Optional[str] = "en"
    timezone: Optional[str] = "UTC"


class UserPreferencesResponse(BaseModel):
    notification_preferences: dict
    privacy_settings: dict
    language: str
    timezone: str
    updated_at: datetime


class UserSearchRequest(BaseModel):
    query: Optional[str] = None
    verified_status: Optional[str] = None
    school: Optional[str] = None
    year: Optional[str] = None
    page: int = 1
    size: int = 20


class UserSearchResponse(BaseModel):
    users: List[UserResponse]
    total: int
    page: int
    size: int
    pages: int
