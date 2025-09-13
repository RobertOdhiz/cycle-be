from datetime import timedelta
import datetime
import secrets
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
    UserProfile,
    ForgotPasswordRequest,
    ResetPasswordRequest
)
from app.schemas.common import ResponseModel
from app.services.email import send_password_reset_email, send_verification_email
from app.services.events import track_event
from fastapi.responses import HTMLResponse


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



@router.get("/verify-email", response_class=HTMLResponse)
async def verify_email(
    token: str,
    db: Session = Depends(get_db)
):
    """Verify email with token - returns HTML response"""
    try:
        user = db.exec(select(User).where(User.id == token)).first()
        
        if not user:
            return HTMLResponse("""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Email Verification Failed - Cycle</title>
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <style>
                        body { 
                            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
                            margin: 0; 
                            padding: 20px; 
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                            min-height: 100vh;
                            display: flex;
                            justify-content: center;
                            align-items: center;
                        }
                        .container { 
                            background: white; 
                            padding: 40px; 
                            border-radius: 12px; 
                            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                            text-align: center;
                            max-width: 500px;
                            width: 100%;
                        }
                        h1 { 
                            color: #333; 
                            margin-bottom: 20px;
                            font-size: 28px;
                        }
                        p { 
                            color: #666; 
                            line-height: 1.6;
                            margin-bottom: 25px;
                            font-size: 16px;
                        }
                        .success { color: #28a745; }
                        .error { color: #dc3545; }
                        .button {
                            background: #667eea;
                            color: white;
                            padding: 12px 30px;
                            text-decoration: none;
                            border-radius: 25px;
                            display: inline-block;
                            margin-top: 15px;
                            font-weight: 600;
                            transition: all 0.3s ease;
                        }
                        .button:hover {
                            background: #5a67d8;
                            transform: translateY(-2px);
                        }
                        .logo {
                            width: 80px;
                            height: 80px;
                            margin-bottom: 20px;
                            background: #667eea;
                            border-radius: 50%;
                            display: inline-flex;
                            align-items: center;
                            justify-content: center;
                            color: white;
                            font-weight: bold;
                            font-size: 24px;
                        }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="logo">C</div>
                        <h1 class="error">Email Verification Failed</h1>
                        <p>Invalid verification token. The link may have expired or is incorrect.</p>
                        <p>Please try requesting a new verification email from the app.</p>
                        <a href="cycleapp://login" class="button">Open Cycle App</a>
                    </div>
                </body>
                </html>
            """)
        
        if user.email_verified:
            return HTMLResponse("""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Email Already Verified - Cycle</title>
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <style>
                        body { 
                            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
                            margin: 0; 
                            padding: 20px; 
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                            min-height: 100vh;
                            display: flex;
                            justify-content: center;
                            align-items: center;
                        }
                        .container { 
                            background: white; 
                            padding: 40px; 
                            border-radius: 12px; 
                            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                            text-align: center;
                            max-width: 500px;
                            width: 100%;
                        }
                        h1 { 
                            color: #333; 
                            margin-bottom: 20px;
                            font-size: 28px;
                        }
                        p { 
                            color: #666; 
                            line-height: 1.6;
                            margin-bottom: 25px;
                            font-size: 16px;
                        }
                        .success { color: #28a745; }
                        .button {
                            background: #667eea;
                            color: white;
                            padding: 12px 30px;
                            text-decoration: none;
                            border-radius: 25px;
                            display: inline-block;
                            margin-top: 15px;
                            font-weight: 600;
                            transition: all 0.3s ease;
                        }
                        .button:hover {
                            background: #5a67d8;
                            transform: translateY(-2px);
                        }
                        .logo {
                            width: 80px;
                            height: 80px;
                            margin-bottom: 20px;
                            background: #28a745;
                            border-radius: 50%;
                            display: inline-flex;
                            align-items: center;
                            justify-content: center;
                            color: white;
                            font-weight: bold;
                            font-size: 24px;
                        }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="logo">✓</div>
                        <h1 class="success">Email Already Verified</h1>
                        <p>Your email address has already been verified successfully.</p>
                        <p>You can now enjoy all features of the Cycle app.</p>
                        <a href="cycleapp://login" class="button">Open Cycle App</a>
                    </div>
                </body>
                </html>
            """)
        
        # Mark email as verified
        user.email_verified = True
        user.verified_status = "verified"
        db.add(user)
        db.commit()
        
        # Track event
        track_event(db, user_id=user.id, event_type="email_verified")
        
        return HTMLResponse(f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Email Verified Successfully - Cycle</title>
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <style>
                    body {{ 
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
                        margin: 0; 
                        padding: 20px; 
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        min-height: 100vh;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                    }}
                    .container {{ 
                        background: white; 
                        padding: 40px; 
                        border-radius: 12px; 
                        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                        text-align: center;
                        max-width: 500px;
                        width: 100%;
                    }}
                    h1 {{ 
                        color: #333; 
                        margin-bottom: 20px;
                        font-size: 28px;
                    }}
                    p {{ 
                        color: #666; 
                        line-height: 1.6;
                        margin-bottom: 25px;
                        font-size: 16px;
                    }}
                    .success {{ color: #28a745; }}
                    .button {{
                        background: #667eea;
                        color: white;
                        padding: 12px 30px;
                        text-decoration: none;
                        border-radius: 25px;
                        display: inline-block;
                        margin-top: 15px;
                        font-weight: 600;
                        transition: all 0.3s ease;
                    }}
                    .button:hover {{
                        background: #5a67d8;
                        transform: translateY(-2px);
                    }}
                    .logo {{
                        width: 80px;
                        height: 80px;
                        margin-bottom: 20px;
                        background: #28a745;
                        border-radius: 50%;
                        display: inline-flex;
                        align-items: center;
                        justify-content: center;
                        color: white;
                        font-weight: bold;
                        font-size: 24px;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="logo">✓</div>
                    <h1 class="success">Email Verified Successfully!</h1>
                    <p>Your email address <strong>{user.email}</strong> has been verified successfully.</p>
                    <p>You can now enjoy all features of the Cycle app.</p>
                    <a href="cycleapp://login" class="button">Open Cycle App</a>
                </div>
            </body>
            </html>
        """)
        
    except Exception as e:
        return HTMLResponse(f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Verification Error - Cycle</title>
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <style>
                    body {{ 
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
                        margin: 0; 
                        padding: 20px; 
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        min-height: 100vh;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                    }}
                    .container {{ 
                        background: white; 
                        padding: 40px; 
                        border-radius: 12px; 
                        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                        text-align: center;
                        max-width: 500px;
                        width: 100%;
                    }}
                    h1 {{ 
                        color: #333; 
                        margin-bottom: 20px;
                        font-size: 28px;
                    }}
                    p {{ 
                        color: #666; 
                        line-height: 1.6;
                        margin-bottom: 25px;
                        font-size: 16px;
                    }}
                    .error {{ color: #dc3545; }}
                    .button {{
                        background: #667eea;
                        color: white;
                        padding: 12px 30px;
                        text-decoration: none;
                        border-radius: 25px;
                        display: inline-block;
                        margin-top: 15px;
                        font-weight: 600;
                        transition: all 0.3s ease;
                    }}
                    .button:hover {{
                        background: #5a67d8;
                        transform: translateY(-2px);
                    }}
                    .logo {{
                        width: 80px;
                        height: 80px;
                        margin-bottom: 20px;
                        background: #dc3545;
                        border-radius: 50%;
                        display: inline-flex;
                        align-items: center;
                        justify-content: center;
                        color: white;
                        font-weight: bold;
                        font-size: 24px;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="logo">!</div>
                    <h1 class="error">Verification Error</h1>
                    <p>Failed to verify your email. Please try again later.</p>
                    <p>Error: {str(e)}</p>
                    <a href="cycleapp://login" class="button">Open Cycle App</a>
                </div>
            </body>
            </html>
        """)


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


@router.post("/forgot-password", response_model=ResponseModel)
async def forgot_password(
    request: ForgotPasswordRequest,
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = None
):
    """Send password reset email"""
    user = db.exec(select(User).where(User.email == request.email)).first()
    if not user:
        # Don't reveal whether email exists for security
        return ResponseModel(
            success=True,
            message="If the email exists, a reset link has been sent"
        )
    
    # Generate reset token (expires in 1 hour)
    reset_token = secrets.token_urlsafe(32)
    user.reset_token = reset_token
    user.reset_token_expires = datetime.datetime.utcnow() + timedelta(hours=1)
    
    db.add(user)
    db.commit()
    
    # Send reset email in background
    if background_tasks:
        background_tasks.add_task(send_password_reset_email, user.email, reset_token)
    else:
        # Fallback: send email synchronously
        send_password_reset_email(user.email, reset_token)
    
    return ResponseModel(
        success=True,
        message="If the email exists, a reset link has been sent"
    )


@router.get("/reset-password", response_class=HTMLResponse)
async def reset_password_page(
    token: str,
    db: Session = Depends(get_db)
):
    """Password reset page - returns HTML form"""
    try:
        # Verify the reset token is valid
        user = db.exec(select(User).where(User.reset_token == token)).first()
        
        if not user or not user.reset_token_expires or user.reset_token_expires < datetime.datetime.utcnow():
            return HTMLResponse("""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Invalid Reset Link - Cycle</title>
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <style>
                        body {{ 
                            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
                            margin: 0; 
                            padding: 20px; 
                            background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
                            min-height: 100vh;
                            display: flex;
                            justify-content: center;
                            align-items: center;
                        }}
                        .container {{ 
                            background: white; 
                            padding: 40px; 
                            border-radius: 12px; 
                            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                            text-align: center;
                            max-width: 500px;
                            width: 100%;
                        }}
                        h1 {{ 
                            color: #333; 
                            margin-bottom: 20px;
                            font-size: 28px;
                        }}
                        p {{ 
                            color: #666; 
                            line-height: 1.6;
                            margin-bottom: 25px;
                            font-size: 16px;
                        }}
                        .error {{ color: #dc3545; }}
                        .button {{
                            background: #ff6b6b;
                            color: white;
                            padding: 12px 30px;
                            text-decoration: none;
                            border-radius: 25px;
                            display: inline-block;
                            margin-top: 15px;
                            font-weight: 600;
                            transition: all 0.3s ease;
                        }}
                        .button:hover {{
                            background: #ee5a24;
                            transform: translateY(-2px);
                        }}
                        .logo {{
                            width: 80px;
                            height: 80px;
                            margin-bottom: 20px;
                            background: #dc3545;
                            border-radius: 50%;
                            display: inline-flex;
                            align-items: center;
                            justify-content: center;
                            color: white;
                            font-weight: bold;
                            font-size: 24px;
                        }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="logo">!</div>
                        <h1 class="error">Invalid Reset Link</h1>
                        <p>This password reset link is invalid or has expired.</p>
                        <p>Please request a new password reset from the app.</p>
                        <a href="cycleapp://forgot-password" class="button">Request New Reset</a>
                    </div>
                </body>
                </html>
            """)
        
        return HTMLResponse(f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Reset Password - Cycle</title>
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <style>
                    body {{ 
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
                        margin: 0; 
                        padding: 20px; 
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        min-height: 100vh;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                    }}
                    .container {{ 
                        background: white; 
                        padding: 40px; 
                        border-radius: 12px; 
                        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                        max-width: 500px;
                        width: 100%;
                    }}
                    h1 {{ 
                        color: #333; 
                        margin-bottom: 20px;
                        font-size: 28px;
                        text-align: center;
                    }}
                    .form-group {{ 
                        margin-bottom: 20px; 
                    }}
                    label {{ 
                        display: block; 
                        margin-bottom: 8px; 
                        font-weight: 600;
                        color: #333;
                    }}
                    input {{ 
                        width: 100%;
                        padding: 12px;
                        border: 2px solid #ddd;
                        border-radius: 8px;
                        font-size: 16px;
                        box-sizing: border-box;
                    }}
                    input:focus {{
                        border-color: #667eea;
                        outline: none;
                    }}
                    .button {{
                        background: #667eea;
                        color: white;
                        padding: 15px;
                        border: none;
                        border-radius: 8px;
                        width: 100%;
                        font-size: 16px;
                        font-weight: 600;
                        cursor: pointer;
                        transition: all 0.3s ease;
                    }}
                    .button:hover {{
                        background: #5a67d8;
                    }}
                    .button:disabled {{
                        background: #ccc;
                        cursor: not-allowed;
                    }}
                    .logo {{
                        width: 80px;
                        height: 80px;
                        margin: 0 auto 20px;
                        background: #667eea;
                        border-radius: 50%;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        color: white;
                        font-weight: bold;
                        font-size: 24px;
                    }}
                    #message {{
                        margin-top: 20px;
                        padding: 15px;
                        border-radius: 8px;
                        display: none;
                    }}
                    .success {{ background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }}
                    .error {{ background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="logo">C</div>
                    <h1>Reset Your Password</h1>
                    
                    <form id="resetForm">
                        <div class="form-group">
                            <label for="password">New Password</label>
                            <input type="password" id="password" name="password" required minlength="6">
                        </div>
                        
                        <div class="form-group">
                            <label for="confirmPassword">Confirm Password</label>
                            <input type="password" id="confirmPassword" name="confirmPassword" required minlength="6">
                        </div>
                        
                        <button type="submit" class="button">Reset Password</button>
                    </form>
                    
                    <div id="message"></div>
                </div>

                <script>
                    document.getElementById('resetForm').addEventListener('submit', async function(e) {{
                        e.preventDefault();
                        
                        const password = document.getElementById('password').value;
                        const confirmPassword = document.getElementById('confirmPassword').value;
                        const messageDiv = document.getElementById('message');
                        const button = document.querySelector('button');
                        
                        // Validate passwords match
                        if (password !== confirmPassword) {{
                            messageDiv.style.display = 'block';
                            messageDiv.className = 'error';
                            messageDiv.innerHTML = 'Passwords do not match!';
                            return;
                        }}
                        
                        // Validate password length
                        if (password.length < 6) {{
                            messageDiv.style.display = 'block';
                            messageDiv.className = 'error';
                            messageDiv.innerHTML = 'Password must be at least 6 characters long!';
                            return;
                        }}
                        
                        button.disabled = true;
                        button.textContent = 'Resetting...';
                        
                        try {{
                            const response = await fetch('https://api.cycle.co.ke/auth/reset-password', {{
                                method: 'POST',
                                headers: {{
                                    'Content-Type': 'application/json',
                                }},
                                body: JSON.stringify({{
                                    token: '{token}',
                                    password: password
                                }})
                            }});
                            
                            const data = await response.json();
                            
                            if (data.success) {{
                                messageDiv.style.display = 'block';
                                messageDiv.className = 'success';
                                messageDiv.innerHTML = 'Password reset successfully! You can now login with your new password.';
                                document.getElementById('resetForm').reset();
                                
                                // Redirect to app after 3 seconds
                                setTimeout(() => {{
                                    window.location.href = 'cycleapp://login';
                                }}, 3000);
                            }} else {{
                                throw new Error(data.message || 'Failed to reset password');
                            }}
                            
                        }} catch (error) {{
                            messageDiv.style.display = 'block';
                            messageDiv.className = 'error';
                            messageDiv.innerHTML = error.message || 'Failed to reset password. Please try again.';
                        }} finally {{
                            button.disabled = false;
                            button.textContent = 'Reset Password';
                        }}
                    }});
                </script>
            </body>
            </html>
        """)
        
    except Exception as e:
        return HTMLResponse(f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Error - Cycle</title>
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <style>
                    body {{ 
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
                        margin: 0; 
                        padding: 20px; 
                        background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
                        min-height: 100vh;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                    }}
                    .container {{ 
                        background: white; 
                        padding: 40px; 
                        border-radius: 12px; 
                        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                        text-align: center;
                        max-width: 500px;
                        width: 100%;
                    }}
                    h1 {{ 
                        color: #333; 
                        margin-bottom: 20px;
                        font-size: 28px;
                    }}
                    p {{ 
                        color: #666; 
                        line-height: 1.6;
                        margin-bottom: 25px;
                        font-size: 16px;
                    }}
                    .error {{ color: #dc3545; }}
                    .button {{
                        background: #ff6b6b;
                        color: white;
                        padding: 12px 30px;
                        text-decoration: none;
                        border-radius: 25px;
                        display: inline-block;
                        margin-top: 15px;
                        font-weight: 600;
                        transition: all 0.3s ease;
                    }}
                    .button:hover {{
                        background: #ee5a24;
                        transform: translateY(-2px);
                    }}
                    .logo {{
                        width: 80px;
                        height: 80px;
                        margin-bottom: 20px;
                        background: #dc3545;
                        border-radius: 50%;
                        display: inline-flex;
                        align-items: center;
                        justify-content: center;
                        color: white;
                        font-weight: bold;
                        font-size: 24px;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="logo">!</div>
                    <h1 class="error">Error</h1>
                    <p>An error occurred while loading the password reset page.</p>
                    <p>Please try again later.</p>
                    <a href="cycleapp://forgot-password" class="button">Try Again</a>
                </div>
            </body>
            </html>
        """)