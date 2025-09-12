from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlmodel import Session, select
from app.database import get_db
from app.models.user import User
from app.models.bike import Bike, BikeStatus
from app.auth import get_current_user, get_current_admin_user
from app.schemas.bike import (
    BikeCreateRequest,
    BikeUpdateRequest,
    BikeResponse,
    BikeListResponse,
    BatchPricingRequest
)
from app.schemas.common import ResponseModel
from app.services.events import track_event
from app.services.cloudinary_service import cloudinary_service

router = APIRouter()


@router.get("/", response_model=ResponseModel[BikeListResponse])
async def get_bikes(
    dock_id: Optional[str] = Query(None, description="Filter by dock ID"),
    type: Optional[str] = Query(None, description="Filter by bike type"),
    status: Optional[str] = Query(None, description="Filter by bike status"),
    db: Session = Depends(get_db)
):
    """Get list of bikes with optional filters"""
    query = select(Bike)
    
    if dock_id:
        query = query.where(Bike.dock_id == dock_id)
    if type:
        query = query.where(Bike.type == type)
    if status:
        query = query.where(Bike.status == status)
    
    bikes = db.exec(query).all()
    
    return ResponseModel(
        success=True,
        data=BikeListResponse(
            bikes=[BikeResponse(
                id=bike.id,
                owner_id=bike.owner_id,
                type=bike.type,
                condition=bike.condition,
                hourly_rate=bike.hourly_rate,
                dock_id=bike.dock_id,
                status=bike.status,
                photos=bike.photos,
                created_at=bike.created_at.isoformat(),
                updated_at=bike.updated_at.isoformat()
            ) for bike in bikes]
        )
    )


@router.post("/owner/bikes", response_model=ResponseModel[BikeResponse])
async def create_bike(
    request: BikeCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new bike (owner only)"""
    # Check if user can own more bikes
    current_bikes = db.exec(select(Bike).where(Bike.owner_id == current_user.id)).count()
    if current_bikes >= current_user.owner_max_bikes:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Maximum bikes limit reached ({current_user.owner_max_bikes})"
        )
    
    # Create bike
    bike = Bike(
        owner_id=current_user.id,
        type=request.type,
        condition=request.condition,
        hourly_rate=request.hourly_rate,
        dock_id=request.dock_id,
        photos=request.photos
    )
    
    db.add(bike)
    db.commit()
    db.refresh(bike)
    
    # Track event
    track_event(db, user_id=current_user.id, bike_id=bike.id, event_type="bike_created")
    
    return ResponseModel(
        success=True,
        data=BikeResponse(
            id=bike.id,
            owner_id=bike.owner_id,
            type=bike.type,
            condition=bike.condition,
            hourly_rate=bike.hourly_rate,
            dock_id=bike.dock_id,
            status=bike.status,
            photos=bike.photos,
            created_at=bike.created_at.isoformat(),
            updated_at=bike.updated_at.isoformat()
        )
    )


@router.patch("/owner/bikes/{bike_id}", response_model=ResponseModel[BikeResponse])
async def update_bike(
    bike_id: str,
    request: BikeUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update bike (owner or admin only)"""
    bike = db.exec(select(Bike).where(Bike.id == bike_id)).first()
    if not bike:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bike not found"
        )
    
    # Check permissions
    if bike.owner_id != current_user.id and current_user.verified_status != "verified":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this bike"
        )
    
    # Update fields
    update_data = request.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(bike, field, value)
    
    db.add(bike)
    db.commit()
    db.refresh(bike)
    
    # Track event
    track_event(db, user_id=current_user.id, bike_id=bike.id, event_type="bike_updated")
    
    return ResponseModel(
        success=True,
        data=BikeResponse(
            id=bike.id,
            owner_id=bike.owner_id,
            type=bike.type,
            condition=bike.condition,
            hourly_rate=bike.hourly_rate,
            dock_id=bike.dock_id,
            status=bike.status,
            photos=bike.photos,
            created_at=bike.created_at.isoformat(),
            updated_at=bike.updated_at.isoformat()
        )
    )


@router.patch("/admin/bikes/batch-pricing", response_model=ResponseModel)
async def batch_update_pricing(
    request: BatchPricingRequest,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Batch update bike pricing (admin only)"""
    # TODO: Implement batch pricing update logic
    # This should respect the policy constraints and not affect open rentals
    
    return ResponseModel(
        success=True,
        message="Batch pricing update completed"
    )


@router.post("/owner/bikes/{bike_id}/photos", response_model=ResponseModel)
async def upload_bike_photo(
    bike_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload a photo for a bike (owner only)"""
    # Get the bike
    bike = db.exec(select(Bike).where(Bike.id == bike_id)).first()
    if not bike:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bike not found"
        )
    
    # Check if user owns the bike
    if bike.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to upload photos for this bike"
        )
    
    # Validate file type (only images)
    allowed_types = ["image/jpeg", "image/jpg", "image/png", "image/gif", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only image files are allowed."
        )
    
    # Validate file size (max 5MB for bike photos)
    file_content = await file.read()
    if len(file_content) > 5 * 1024 * 1024:  # 5MB
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size too large. Maximum size is 5MB."
        )
    
    # Reset file pointer
    await file.seek(0)
    
    try:
        # Upload photo to Cloudinary
        upload_result = await cloudinary_service.upload_bike_photo(file, bike_id)
        
        # Update bike photos list
        if bike.photos is None:
            bike.photos = []
        
        bike.photos.append(upload_result["secure_url"])
        db.add(bike)
        db.commit()
        
        # Track event
        track_event(db, user_id=current_user.id, bike_id=bike.id, event_type="bike_photo_uploaded")
        
        return ResponseModel(
            success=True,
            message="Bike photo uploaded successfully",
            data={
                "cloudinary_url": upload_result["secure_url"],
                "public_id": upload_result["public_id"],
                "photos_count": len(bike.photos)
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload bike photo: {str(e)}"
        )


@router.delete("/owner/bikes/{bike_id}/photos", response_model=ResponseModel)
async def delete_bike_photo(
    bike_id: str,
    photo_url: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a photo from a bike (owner only)"""
    # Get the bike
    bike = db.exec(select(Bike).where(Bike.id == bike_id)).first()
    if not bike:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bike not found"
        )
    
    # Check if user owns the bike
    if bike.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete photos for this bike"
        )
    
    # Check if photo exists in bike photos
    if not bike.photos or photo_url not in bike.photos:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Photo not found"
        )
    
    try:
        # Extract public_id from Cloudinary URL
        # Cloudinary URLs format: https://res.cloudinary.com/cloud_name/image/upload/v1234567890/public_id.jpg
        public_id = photo_url.split('/')[-1].split('.')[0]
        
        # Delete from Cloudinary
        delete_result = await cloudinary_service.delete_file(public_id)
        
        # Remove from bike photos list
        bike.photos.remove(photo_url)
        db.add(bike)
        db.commit()
        
        # Track event
        track_event(db, user_id=current_user.id, bike_id=bike.id, event_type="bike_photo_deleted")
        
        return ResponseModel(
            success=True,
            message="Bike photo deleted successfully",
            data={
                "deleted_url": photo_url,
                "photos_count": len(bike.photos) if bike.photos else 0
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete bike photo: {str(e)}"
        )

@router.get("/{bike_id}", response_model=ResponseModel[BikeResponse])
async def get_bike_by_id(
    bike_id: str,
    db: Session = Depends(get_db)
):
    """Get a bike by ID"""
    bike = db.get(Bike, bike_id)
    return ResponseModel(
        success=True,
        data=bike)

@router.get("/find/nearby", response_model=ResponseModel[BikeListResponse])
async def get_bikes_nearby(
    latitude: float = Query(..., description="Latitude coordinate"),
    longitude: float = Query(..., description="Longitude coordinate"),
    radius: float = Query(1.0, description="Search radius in kilometers"),
    db: Session = Depends(get_db)
):
    """Get bikes nearby"""
    if radius <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Radius must be a positive number"
        )
    bikes = db.exec(select(Bike).where(Bike.geom.distance(latitude, longitude) <= radius)).all()
    return ResponseModel(
        success=True,
        data=BikeListResponse(
            bikes=[BikeResponse(
                id=bike.id,
                owner_id=bike.owner_id,
                type=bike.type,
                condition=bike.condition,
                hourly_rate=bike.hourly_rate,
                dock_id=bike.dock_id,
                status=bike.status,
                photos=bike.photos,
                created_at=bike.created_at.isoformat(),
                updated_at=bike.updated_at.isoformat()
            ) for bike in bikes]
        )
    )

@router.patch("/{bike_id}", response_model=ResponseModel)
async def update_bike(
    bike_id: str,
    bike: Bike,
    db: Session = Depends(get_db)
):
    """Update a bike"""
    bike = db.get(Bike, bike_id)
    bike.type = bike.type
    db.commit()
    return ResponseModel(
        success=True,
        message="Bike updated successfully"
    )

@router.delete("/{bike_id}", response_model=ResponseModel)
async def delete_bike(
    bike_id: str,
    db: Session = Depends(get_db)
):
    """Delete a bike"""
    bike = db.get(Bike, bike_id)
    db.delete(bike)
    db.commit()
    return ResponseModel(
        success=True,
        message="Bike deleted successfully"
    )

@router.post("/{bike_id}/lock", response_model=ResponseModel)
async def lock_bike(
    bike_id: str,
    db: Session = Depends(get_db)
):
    """Lock a bike"""
    bike = db.get(Bike, bike_id)
    bike.status = BikeStatus.locked
    db.commit()
    return ResponseModel(
        success=True,
        message="Bike locked successfully"
    )

@router.post("/{bike_id}/unlock", response_model=ResponseModel)
async def unlock_bike(
    bike_id: str,
    db: Session = Depends(get_db)
):
    """Unlock a bike"""
    bike = db.get(Bike, bike_id)
    bike.status = BikeStatus.unlocked
    db.commit()
    return ResponseModel(
        success=True,
        message="Bike unlocked successfully"
    )

@router.post("/{bike_id}/rent", response_model=ResponseModel)
async def rent_bike(
    bike_id: str,
    db: Session = Depends(get_db)
):
    """Rent a bike"""
    bike = db.get(Bike, bike_id)
    bike.status = BikeStatus.rented
    db.commit()
    return ResponseModel(
        success=True,
        message="Bike rented successfully"
    )

@router.post("/{bike_id}/return", response_model=ResponseModel)
async def return_bike(
    bike_id: str,
    db: Session = Depends(get_db)
):
    """Return a bike"""
    bike = db.get(Bike, bike_id)
    bike.status = BikeStatus.available
    db.commit()
    return ResponseModel(
        success=True,
        message="Bike returned successfully"
    )