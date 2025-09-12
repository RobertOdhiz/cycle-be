from typing import Optional, Dict, Any
from sqlmodel import Session
from app.models.event import Event
from uuid import UUID


def track_event(
    db: Session,
    user_id: Optional[UUID] = None,
    bike_id: Optional[UUID] = None,
    dock_id: Optional[UUID] = None,
    event_type: str = "",
    properties: Optional[Dict[str, Any]] = None
) -> Event:
    """Track an analytics event"""
    event = Event(
        user_id=user_id,
        bike_id=bike_id,
        dock_id=dock_id,
        event_type=event_type,
        properties=properties or {}
    )
    
    db.add(event)
    db.commit()
    db.refresh(event)
    
    return event
