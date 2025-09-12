from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from app.database import get_db
from app.models.user import User
from app.models.event import Event
from app.auth import get_current_user
from app.schemas.common import ResponseModel
from typing import List, Dict, Any
from datetime import datetime

router = APIRouter()


@router.post("/events", response_model=ResponseModel)
async def sync_events(
    events: List[Dict[str, Any]],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Bulk sync events from client"""
    # Validate and insert events
    event_objects = []
    for event_data in events:
        event = Event(
            user_id=event_data.get("user_id"),
            bike_id=event_data.get("bike_id"),
            dock_id=event_data.get("dock_id"),
            event_type=event_data["event_type"],
            properties=event_data.get("properties", {}),
            occurred_at=event_data.get("occurred_at")
        )
        event_objects.append(event)
    
    db.add_all(event_objects)
    db.commit()
    
    return ResponseModel(
        success=True,
        data={"inserted_count": len(events)}
    )


@router.post("/devices", response_model=ResponseModel)
async def register_device(
    expo_push_token: str,
    platform: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Register device for push notifications"""
    from app.models.device import Device
    
    # Check if device already exists
    existing_device = db.exec(
        select(Device).where(
            Device.user_id == current_user.id,
            Device.expo_push_token == expo_push_token
        )
    ).first()
    
    if existing_device:
        # Update last seen
        existing_device.last_seen = datetime.utcnow()
        db.add(existing_device)
    else:
        # Create new device
        device = Device(
            user_id=current_user.id,
            expo_push_token=expo_push_token,
            platform=platform
        )
        db.add(device)
    
    db.commit()
    
    return ResponseModel(
        success=True,
        message="Device registered successfully"
    )
