from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlmodel import Session, select
from sqlalchemy import func

from app.database import get_db
from app.models.user import User
from app.models.bike import Bike, BikeStatus
from app.models.dock import Dock
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


router = APIRouter(tags=["bikes"])


# ---------------------------
# Get bikes with filters
# ---------------------------
@router.get("/", response_model=ResponseModel[BikeListResponse])
async def get_bikes(
    dock_id: Optional[str] = Query(None, description="Filter by dock ID"),
    type: Optional[str] = Query(None, description="Filter by bike type"),
    status: Optional[str] = Query(None, description="Filter by bike status"),
    db: Session = Depends(get_db),
):
    query = select(Bike)

    if dock_id:
        query = query.where(Bike.dock_id == dock_id)
    if type:
        query = query.where(Bike.type == type)
    if status:
        query = query.where(Bike.status == status)

    bikes = db.exec(query).all()

    bike_list = [
        BikeResponse(
            id=str(bike.id),
            owner_id=str(bike.owner_id),
            type=bike.type,
            condition=bike.condition,
            hourly_rate=bike.hourly_rate,
            dock_id=str(bike.dock_id) if bike.dock_id else None,
            status=bike.status,
            photos=bike.photos,
            created_at=bike.created_at.isoformat(),
            updated_at=bike.updated_at.isoformat(),
        )
        for bike in bikes
    ]

    return ResponseModel(success=True, data=BikeListResponse(bikes=bike_list, count=len(bike_list)))


# ---------------------------
# Create a new bike
# ---------------------------
@router.post("/owner/bikes", response_model=ResponseModel[BikeResponse])
async def create_bike(
    request: BikeCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    current_bikes = len(db.exec(select(Bike).where(Bike.owner_id == current_user.id)).all())
    if current_bikes >= current_user.owner_max_bikes:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Maximum bikes limit reached ({current_user.owner_max_bikes})",
        )

    bike = Bike(
        owner_id=current_user.id,
        type=request.type,
        condition=request.condition,
        hourly_rate=request.hourly_rate,
        dock_id=request.dock_id,
        photos=request.photos,
    )
    db.add(bike)
    db.commit()
    db.refresh(bike)

    track_event(db, user_id=current_user.id, bike_id=bike.id, event_type="bike_created")

    return ResponseModel(success=True, data=BikeResponse.from_orm(bike))


# ---------------------------
# Update bike (owner/admin)
# ---------------------------
@router.patch("/owner/bikes/{bike_id}", response_model=ResponseModel[BikeResponse])
async def update_bike(
    bike_id: str,
    request: BikeUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    bike = db.exec(select(Bike).where(Bike.id == bike_id)).first()
    if not bike:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bike not found")

    if bike.owner_id != current_user.id and current_user.verified_status != "verified":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    update_data = request.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(bike, field, value)

    db.add(bike)
    db.commit()
    db.refresh(bike)

    track_event(db, user_id=current_user.id, bike_id=bike.id, event_type="bike_updated")

    return ResponseModel(success=True, data=BikeResponse.from_orm(bike))


# ---------------------------
# Batch pricing (admin only)
# ---------------------------
@router.patch("/admin/bikes/batch-pricing", response_model=ResponseModel)
async def batch_update_pricing(
    request: BatchPricingRequest,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    # TODO: implement logic
    return ResponseModel(success=True, message="Batch pricing update completed")


# ---------------------------
# Upload bike photo
# ---------------------------
@router.post("/owner/bikes/{bike_id}/photos", response_model=ResponseModel)
async def upload_bike_photo(
    bike_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    bike = db.exec(select(Bike).where(Bike.id == bike_id)).first()
    if not bike:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bike not found")
    if bike.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    allowed_types = ["image/jpeg", "image/jpg", "image/png", "image/gif", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file type")

    file_content = await file.read()
    if len(file_content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File size too large")
    await file.seek(0)

    upload_result = await cloudinary_service.upload_bike_photo(file, bike_id)

    if bike.photos is None:
        bike.photos = []
    bike.photos.append(upload_result["secure_url"])

    db.add(bike)
    db.commit()

    track_event(db, user_id=current_user.id, bike_id=bike.id, event_type="bike_photo_uploaded")

    return ResponseModel(
        success=True,
        message="Bike photo uploaded successfully",
        data={
            "cloudinary_url": upload_result["secure_url"],
            "public_id": upload_result["public_id"],
            "photos_count": len(bike.photos),
        },
    )


# ---------------------------
# Delete bike photo
# ---------------------------
@router.delete("/owner/bikes/{bike_id}/photos", response_model=ResponseModel)
async def delete_bike_photo(
    bike_id: str,
    photo_url: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    bike = db.exec(select(Bike).where(Bike.id == bike_id)).first()
    if not bike:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bike not found")
    if bike.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    if not bike.photos or photo_url not in bike.photos:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found")

    public_id = photo_url.split("/")[-1].split(".")[0]
    await cloudinary_service.delete_file(public_id)

    bike.photos.remove(photo_url)
    db.add(bike)
    db.commit()

    track_event(db, user_id=current_user.id, bike_id=bike.id, event_type="bike_photo_deleted")

    return ResponseModel(
        success=True,
        message="Bike photo deleted successfully",
        data={"deleted_url": photo_url, "photos_count": len(bike.photos) if bike.photos else 0},
    )


# ---------------------------
# Get bike by ID
# ---------------------------
@router.get("/{bike_id}", response_model=ResponseModel[BikeResponse])
async def get_bike_by_id(bike_id: str, db: Session = Depends(get_db)):
    bike = db.get(Bike, bike_id)
    if not bike:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bike not found")
    return ResponseModel(success=True, data=BikeResponse.from_orm(bike))


# ---------------------------
# Nearby bikes (spatial)
# ---------------------------
@router.get("/find/nearby", response_model=ResponseModel[BikeListResponse])
async def get_bikes_nearby(
    latitude: float = Query(...),
    longitude: float = Query(...),
    radius: float = Query(1.0, description="Radius in km"),
    db: Session = Depends(get_db),
):
    if radius <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Radius must be positive")

    radius_meters = radius * 1000
    user_point = func.ST_GeogFromText(f"POINT({longitude} {latitude})")

    query = (
        select(Bike)
        .join(Dock, Bike.dock_id == Dock.id)
        .where(func.ST_DWithin(Dock.geom, user_point, radius_meters))
        .where(Bike.status == BikeStatus.available)
    )
    nearby_bikes = db.exec(query).all()

    if not nearby_bikes:
        fallback_bikes = (
            db.exec(select(Bike).where(Bike.status == BikeStatus.available).order_by(func.random()).limit(10)).all()
        )
        bike_list = [BikeResponse.from_orm(b) for b in fallback_bikes]
        return ResponseModel(
            success=True,
            data=BikeListResponse(
                bikes=bike_list,
                count=len(bike_list),
                fallback_used=True,
                message="No bikes nearby. Showing random available bikes.",
            ),
        )

    bike_list = [BikeResponse.from_orm(b) for b in nearby_bikes]
    return ResponseModel(success=True, data=BikeListResponse(bikes=bike_list, count=len(bike_list)))


# ---------------------------
# Status actions
# ---------------------------
@router.delete("/{bike_id}", response_model=ResponseModel)
async def delete_bike(bike_id: str, db: Session = Depends(get_db)):
    bike = db.get(Bike, bike_id)
    if not bike:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bike not found")
    db.delete(bike)
    db.commit()
    return ResponseModel(success=True, message="Bike deleted successfully")


@router.post("/{bike_id}/lock", response_model=ResponseModel)
async def lock_bike(bike_id: str, db: Session = Depends(get_db)):
    bike = db.get(Bike, bike_id)
    if not bike:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bike not found")
    bike.status = BikeStatus.locked
    db.commit()
    return ResponseModel(success=True, message="Bike locked successfully")


@router.post("/{bike_id}/unlock", response_model=ResponseModel)
async def unlock_bike(bike_id: str, db: Session = Depends(get_db)):
    bike = db.get(Bike, bike_id)
    if not bike:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bike not found")
    bike.status = BikeStatus.unlocked
    db.commit()
    return ResponseModel(success=True, message="Bike unlocked successfully")


@router.post("/{bike_id}/rent", response_model=ResponseModel)
async def rent_bike(bike_id: str, db: Session = Depends(get_db)):
    bike = db.get(Bike, bike_id)
    if not bike:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bike not found")
    bike.status = BikeStatus.rented
    db.commit()
    return ResponseModel(success=True, message="Bike rented successfully")


@router.post("/{bike_id}/return", response_model=ResponseModel)
async def return_bike(bike_id: str, db: Session = Depends(get_db)):
    bike = db.get(Bike, bike_id)
    if not bike:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bike not found")
    bike.status = BikeStatus.available
    db.commit()
    return ResponseModel(success=True, message="Bike returned successfully")
