from datetime import timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlmodel import Session, select
from app.database import get_db
from app.models.user import User
from app.models.event import Event
from app.auth import (
    get_password_hash, 
    verify_password, 
    create_access_token, 
    create_refresh_token,
    get_current_user
)
from app.schemas.auth import (
    SignupRequest, 
    SignupResponse, 
    LoginRequest, 
    LoginResponse,
    RefreshRequest,
    RefreshResponse,
    ResendVerificationRequest,
    VerifyEmailRequest,
    UserProfile
)
from app.schemas.common import ResponseModel
from app.services.email import send_verification_email
from app.services.events import track_event

router = APIRouter()


@router.post("/signup", response_model=ResponseModel[SignupResponse])
async def signup(
    request: SignupRequest,
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = None
):
    """User signup endpoint"""
    # Check if user already exists
    existing_user = db.exec(select(User).where(User.email == request.email)).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user
    user = User(
        email=request.email,
        password_hash=get_password_hash(request.password),
        name=request.name,
        phone=request.phone,
        school=request.school,
        year=request.year
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Send verification email in background
    if background_tasks:
        background_tasks.add_task(send_verification_email, user.email, user.id)
    
    # Track event
    track_event(db, user_id=user.id, event_type="user_signup")
    
    return ResponseModel(
        success=True,
        data=SignupResponse(
            user_id=user.id,
            email=user.email
        )
    )


@router.post("/login", response_model=ResponseModel[LoginResponse])
async def login(
    request: LoginRequest,
    db: Session = Depends(get_db)
):
    """User login endpoint"""
    # Find user
    user = db.exec(select(User).where(User.email == request.email)).first()
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Create tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    # Track event
    track_event(db, user_id=user.id, event_type="user_login")
    
    return ResponseModel(
        success=True,
        data=LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user={
                "name": user.name,
                "id": str(user.id),
                "email": user.email,
                "verified_status": user.verified_status,
                "eco_points": user.eco_points
            }
        )
    )


@router.post("/refresh", response_model=ResponseModel[RefreshResponse])
async def refresh_token(
    request: RefreshRequest,
    db: Session = Depends(get_db)
):
    """Refresh access token"""
    from app.auth.jwt import verify_token
    
    payload = verify_token(request.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    user_id = payload.get("sub")
    user = db.exec(select(User).where(User.id == user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    access_token = create_access_token(data={"sub": str(user.id)})
    
    return ResponseModel(
        success=True,
        data=RefreshResponse(access_token=access_token)
    )


@router.post("/resend-verification", response_model=ResponseModel)
async def resend_verification(
    request: ResendVerificationRequest,
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = None
):
    """Resend verification email"""
    user = db.exec(select(User).where(User.email == request.email)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already verified"
        )
    
    # Send verification email in background
    if background_tasks:
        background_tasks.add_task(send_verification_email, user.email, user.id)
    
    return ResponseModel(
        success=True,
        message="Verification email sent"
    )


@router.get("/verify-email")
async def verify_email(
    token: str,
    db: Session = Depends(get_db)
):
    """Verify email with token"""
    # TODO: Implement token verification logic
    # For now, just return success
    return ResponseModel(
        success=True,
        message="Email verified successfully"
    )


@router.get("/me", response_model=ResponseModel[UserProfile])
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """Get current user profile"""
    return ResponseModel(
        success=True,
        data=UserProfile(
            id=current_user.id,
            email=current_user.email,
            email_verified=current_user.email_verified,
            name=current_user.name,
            phone=current_user.phone,
            school=current_user.school,
            year=current_user.year,
            verified_status=current_user.verified_status,
            eco_points=current_user.eco_points,
            owner_max_bikes=current_user.owner_max_bikes,
            created_at=current_user.created_at.isoformat(),
            updated_at=current_user.updated_at.isoformat()
        )
    )
