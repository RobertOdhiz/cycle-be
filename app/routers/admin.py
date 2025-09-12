from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from app.database import get_db
from app.models.user import User
from app.models.event import Event
from app.auth import get_current_admin_user
from app.schemas.common import ResponseModel

router = APIRouter()


@router.get("/analytics/dau", response_model=ResponseModel)
async def get_dau(
    date: str = None,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get Daily Active Users"""
    # TODO: Implement DAU calculation from events table
    # SELECT COUNT(DISTINCT user_id) FROM events WHERE event_type = 'ride_start' AND DATE(occurred_at) = date
    
    return ResponseModel(
        success=True,
        data={"dau": 0, "date": date or "today"}
    )


@router.get("/analytics/trips_per_dock", response_model=ResponseModel)
async def get_trips_per_dock(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get trips per dock"""
    # TODO: Implement trips per dock calculation
    
    return ResponseModel(
        success=True,
        data={"trips_per_dock": []}
    )


@router.patch("/users/{user_id}/policy", response_model=ResponseModel)
async def update_user_policy(
    user_id: str,
    owner_max_bikes: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Update user policy (admin only)"""
    user = db.exec(select(User).where(User.id == user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.owner_max_bikes = owner_max_bikes
    db.add(user)
    db.commit()
    
    return ResponseModel(
        success=True,
        message="User policy updated"
    )


@router.post("/payouts/{payout_id}/approve", response_model=ResponseModel)
async def approve_payout(
    payout_id: str,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Approve payout (admin only)"""
    # TODO: Implement payout approval logic
    
    return ResponseModel(
        success=True,
        message="Payout approved"
    )
