from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlmodel import Session, select
from app.database import get_db
from app.models.user import User
from app.models.verification_doc import VerificationDoc
from app.auth import get_current_user, get_current_admin_user
from app.schemas.common import ResponseModel
from app.services.events import track_event
from app.services.cloudinary_service import cloudinary_service
from datetime import datetime

router = APIRouter()


@router.post("/submit", response_model=ResponseModel)
async def submit_verification(
    user_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit verification document"""
    # Validate file type
    allowed_types = ["image/jpeg", "image/jpg", "image/png", "application/pdf"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only JPEG, PNG, and PDF files are allowed."
        )
    
    # Validate file size (max 10MB)
    file_content = await file.read()
    if len(file_content) > 10 * 1024 * 1024:  # 10MB
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size too large. Maximum size is 10MB."
        )
    
    # Reset file pointer
    await file.seek(0)
    
    try:
        # Upload file to Cloudinary
        upload_result = await cloudinary_service.upload_verification_document(file, user_id)
        
        # Create verification document
        doc = VerificationDoc(
            user_id=user_id,
            cloudinary_url=upload_result["secure_url"]
        )
        
        # Update user status
        user = db.exec(select(User).where(User.id == user_id)).first()
        if user:
            user.verified_status = "pending"
            db.add(user)
        
        db.add(doc)
        db.commit()
        
        # Track event
        track_event(db, user_id=user_id, event_type="verification_submitted")
        
        return ResponseModel(
            success=True,
            message="Verification document submitted successfully",
            data={
                "document_id": str(doc.id),
                "cloudinary_url": upload_result["secure_url"],
                "public_id": upload_result["public_id"]
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit verification document: {str(e)}"
        )


@router.post("/upload", response_model=ResponseModel)
async def upload_file(
    file: UploadFile = File(...),
    folder: str = "general",
    current_user: User = Depends(get_current_user)
):
    """Upload a file to Cloudinary"""
    # Validate file type
    allowed_types = [
        "image/jpeg", "image/jpg", "image/png", "image/gif", "image/webp",
        "application/pdf", "text/plain", "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Allowed types: images, PDF, and documents."
        )
    
    # Validate file size (max 20MB)
    file_content = await file.read()
    if len(file_content) > 20 * 1024 * 1024:  # 20MB
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size too large. Maximum size is 20MB."
        )
    
    # Reset file pointer
    await file.seek(0)
    
    try:
        # Upload file to Cloudinary
        upload_result = await cloudinary_service.upload_file(file, folder)
        
        return ResponseModel(
            success=True,
            message="File uploaded successfully",
            data={
                "cloudinary_url": upload_result["secure_url"],
                "public_id": upload_result["public_id"],
                "format": upload_result.get("format"),
                "bytes": upload_result.get("bytes")
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}"
        )


@router.post("/nudge", response_model=ResponseModel)
async def nudge_verification(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Nudge verification if pending too long"""
    # TODO: Implement verification nudge logic
    
    return ResponseModel(
        success=True,
        message="Verification nudge sent"
    )


@router.patch("/admin/{user_id}", response_model=ResponseModel)
async def approve_verification(
    user_id: str,
    status: str,
    notes: str = None,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Approve/reject verification (admin only)"""
    # Update user status
    user = db.exec(select(User).where(User.id == user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.verified_status = status
    db.add(user)
    
    # Update verification document
    doc = db.exec(select(VerificationDoc).where(VerificationDoc.user_id == user_id)).first()
    if doc:
        doc.status = status
        doc.reviewed_by = current_user.id
        doc.reviewed_at = datetime.utcnow()
        doc.notes = notes
        db.add(doc)
    
    db.commit()
    
    # Track event
    track_event(db, user_id=user_id, event_type="verification_completed")
    
    return ResponseModel(
        success=True,
        message=f"Verification {status}"
    )
