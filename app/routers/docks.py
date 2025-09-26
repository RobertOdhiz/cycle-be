from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from app.database import get_db
from app.models.user import User
from app.models.dock import Dock
from app.models.event import Event
from app.services.events import track_event
from app.auth import get_current_admin_user
from app.schemas.common import ResponseModel
from fastapi import Query
from geoalchemy2 import WKTElement

router = APIRouter()


@router.get("/", response_model=ResponseModel)
async def get_docks(
    lat: float = None,
    lng: float = None,
    radius: float = None,
    since: str = None,
    db: Session = Depends(get_db)
):
    """Get docks with optional location filtering"""
    # TODO: Implement PostGIS spatial queries
    docks = db.exec(select(Dock)).all()
    
    return ResponseModel(
        success=True,
        data={"docks": [
            {
                "id": str(dock.id),
                "name": dock.name,
                "capacity": dock.capacity,
                "available_count": dock.available_count
            } for dock in docks
        ]}
    )


@router.post("/admin", response_model=ResponseModel)
async def create_dock(
    name: str,
    lat: float,
    lng: float,
    capacity: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Create a new dock (admin only)"""
    # Create a point geometry from lat/lng
    point = WKTElement(f'POINT({lng} {lat})', srid=4326)
    
    dock = Dock(
        name=name,
        geom=point,  # This was missing!
        capacity=capacity,
        available_count=0  # Default to 0 available bikes
    )
    
    db.add(dock)
    db.commit()
    db.refresh(dock)
    
    # Emit dock event
    track_event(db, user_id=current_user.id, event_type="dock_created", properties={"dock_id": str(dock.id), "name": dock.name})
    
    return ResponseModel(
        success=True,
        message="Dock created successfully",
        data={"dock_id": str(dock.id)}
    )


@router.get("/{dock_id}", response_model=ResponseModel)
async def get_dock_by_id(
    dock_id: str,
    db: Session = Depends(get_db)
):
    """Get a dock by ID"""
    dock = db.get(Dock, dock_id)
    return ResponseModel(
        success=True,
        data=dock)

@router.get("/find/nearby", response_model=ResponseModel)
async def get_docks_nearby(
    latitude: float = Query(..., description="Latitude coordinate"),
    longitude: float = Query(..., description="Longitude coordinate"),
    radius: float = Query(1.0, description="Search radius in kilometers"),
    db: Session = Depends(get_db)
):
    """Get docks nearby"""
    if radius <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Radius must be a positive number"
        )
    docks = db.exec(select(Dock).where(Dock.geom.distance(latitude, longitude) <= radius)).all()
    return ResponseModel(
        success=True,
        data=docks)

@router.patch("/{dock_id}", response_model=ResponseModel)
async def update_dock(
    dock_id: str,
    dock_data: dict,  # Should be a Pydantic model instead of Dock instance
    current_user: User = Depends(get_current_admin_user),  # Add admin protection
    db: Session = Depends(get_db)
):
    """Update a dock (admin only)"""
    dock = db.get(Dock, dock_id)
    if not dock:
        raise HTTPException(status_code=404, detail="Dock not found")
    
    # Update fields if provided
    if 'name' in dock_data:
        dock.name = dock_data['name']
    if 'capacity' in dock_data:
        dock.capacity = dock_data['capacity']
    if 'lat' in dock_data and 'lng' in dock_data:
        # Update geometry if coordinates provided
        point = WKTElement(f'POINT({dock_data["lng"]} {dock_data["lat"]})', srid=4326)
        dock.geom = point
    
    db.commit()
    db.refresh(dock)
    
    track_event(db, user_id=current_user.id, event_type="dock_updated", properties={"dock_id": str(dock_id)})
    
    return ResponseModel(
        success=True,
        message="Dock updated successfully"
    )

@router.delete("/{dock_id}", response_model=ResponseModel)
async def delete_dock(
    dock_id: str,
    db: Session = Depends(get_db)
):
    """Delete a dock"""
    dock = db.get(Dock, dock_id)
    db.delete(dock)
    db.commit()
    # Emit dock event
    track_event(db, event_type="dock_deleted", properties={"dock_id": str(dock_id)})
    return ResponseModel(
        success=True,
        message="Dock deleted successfully"
    )