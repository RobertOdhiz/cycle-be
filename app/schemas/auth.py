from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from uuid import UUID


class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    name: str
    phone: Optional[str] = None
    school: Optional[str] = None
    year: Optional[str] = None


class SignupResponse(BaseModel):
    user_id: UUID
    email: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    user: dict


class RefreshRequest(BaseModel):
    refresh_token: str


class RefreshResponse(BaseModel):
    access_token: str


class ResendVerificationRequest(BaseModel):
    email: EmailStr


class VerifyEmailRequest(BaseModel):
    token: str


class UserProfile(BaseModel):
    id: UUID
    email: str
    email_verified: bool
    name: Optional[str] = None
    phone: Optional[str] = None
    school: Optional[str] = None
    year: Optional[str] = None
    verified_status: str
    eco_points: int
    owner_max_bikes: int
    created_at: str
    updated_at: str

class ForgotPasswordRequest(BaseModel):
    email: str

class ResetPasswordRequest(BaseModel):
    token: str
    password: str