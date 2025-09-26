from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from sqlalchemy import func, cast, Date
from app.database import get_db
from app.models.user import User, UserRole
from app.models.event import Event
from app.models.bike import Bike, BikeStatus
from app.models.dock import Dock
from app.models.zone import Zone
from app.models.rental import Rental
from app.models.payment import Payment, PaymentStatus
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


@router.get("/dau", response_model=ResponseModel)
async def get_dau_simple(
    date: str = None,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get Daily Active Users (distinct users with any event on a given date)."""
    try:
        if date:
            # Expecting YYYY-MM-DD
            from datetime import datetime
            day = datetime.strptime(date, "%Y-%m-%d").date()
        else:
            from datetime import datetime, timezone
            day = datetime.now(timezone.utc).date()
        # COUNT(DISTINCT user_id) WHERE DATE(occurred_at) = day
        stmt = select(func.count(func.distinct(Event.user_id))).where(cast(Event.occurred_at, Date) == day)
        dau = db.exec(stmt).one() or 0
        return ResponseModel(success=True, data={"dau": int(dau), "date": str(day)})
    except Exception as e:
        return ResponseModel(success=False, error=str(e))


@router.get("/analytics/trips_per_dock", response_model=ResponseModel)
async def get_trips_per_dock(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get trips per dock"""
    # Approximate trips per dock using events with event_type 'ride_start'
    try:
        subq = (
            select(Event.dock_id, func.count(Event.id).label("trips"))
            .where(Event.event_type == "ride_start", Event.dock_id.isnot(None))
            .group_by(Event.dock_id)
            .subquery()
        )

        rows = db.exec(
            select(
                Dock.id,
                Dock.name,
                Dock.capacity,
                Dock.available_count,
                subq.c.trips,
            ).join(subq, subq.c.dock_id == Dock.id, isouter=True)
        ).all()

        trips_per_dock = [
            {
                "dock_id": str(row[0]),
                "dock_name": row[1],
                "trips": int(row[4] or 0),
                "location": None,
            }
            for row in rows
        ]

        return ResponseModel(success=True, data={"trips_per_dock": trips_per_dock})
    except Exception as e:
        return ResponseModel(success=False, error=str(e))


@router.get("/analytics/revenue", response_model=ResponseModel)
async def get_revenue_overview(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get revenue aggregates for daily/weekly/monthly successful payments."""
    try:
        from datetime import datetime, timedelta, timezone
        now = datetime.now(timezone.utc)
        start_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        start_week = start_day - timedelta(days=start_day.weekday())
        start_month = start_day.replace(day=1)

        def sum_between(start):
            stmt = (
                select(func.coalesce(func.sum(Payment.amount), 0))
                .where(
                    Payment.status == PaymentStatus.success,
                    Payment.created_at >= start,
                )
            )
            return db.exec(stmt).one() or 0

        daily = float(sum_between(start_day))
        weekly = float(sum_between(start_week))
        monthly = float(sum_between(start_month))

        return ResponseModel(success=True, data={"daily": daily, "weekly": weekly, "monthly": monthly})
    except Exception as e:
        return ResponseModel(success=False, error=str(e))


@router.get("/overview", response_model=ResponseModel)
async def get_admin_overview(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Overview metrics for dashboard home."""
    try:
        from datetime import datetime, timezone
        today = datetime.now(timezone.utc).date()

        total_bikes = db.exec(select(func.count(Bike.id))).one() or 0
        active_bikes = db.exec(
            select(func.count(Bike.id)).where(Bike.status.in_([BikeStatus.available, BikeStatus.rented]))
        ).one() or 0

        total_docks = db.exec(select(func.count(Dock.id))).one() or 0
        available_docks = db.exec(select(func.coalesce(func.sum(Dock.available_count), 0))).one() or 0

        active_zones = db.exec(select(func.count(Zone.id))).one() or 0

        today_trips = db.exec(
            select(func.count(Rental.id)).where(cast(Rental.start_at, Date) == today)
        ).one() or 0

        today_revenue = db.exec(
            select(func.coalesce(func.sum(Payment.amount), 0)).where(
                Payment.status == PaymentStatus.success,
                cast(Payment.created_at, Date) == today,
            )
        ).one() or 0

        # Basic growth placeholder: compare to previous day trips
        from datetime import timedelta
        yesterday = today - timedelta(days=1)
        yesterday_trips = db.exec(
            select(func.count(Rental.id)).where(cast(Rental.start_at, Date) == yesterday)
        ).one() or 0
        growth = 0.0
        try:
            if yesterday_trips:
                growth = ((int(today_trips) - int(yesterday_trips)) / float(yesterday_trips)) * 100.0
        except Exception:
            growth = 0.0

        return ResponseModel(
            success=True,
            data={
                "totalBikes": int(total_bikes),
                "activeBikes": int(active_bikes),
                "totalDocks": int(total_docks),
                "availableDocks": int(available_docks),
                "activeZones": int(active_zones),
                "todayTrips": int(today_trips),
                "revenue": float(today_revenue),
                "growth": round(growth, 2),
            },
        )
    except Exception as e:
        return ResponseModel(success=False, error=str(e))


@router.get("/activities", response_model=ResponseModel)
async def get_recent_activities(
    limit: int = 10,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Recent activity derived from events."""
    try:
        events = db.exec(
            select(Event).order_by(Event.occurred_at.desc()).limit(limit)
        ).all()
        def to_action(e: Event):
            mapping = {
                "ride_start": "Ride started",
                "ride_end": "Ride ended",
                "bike_added": "New bike added",
                "dock_updated": "Dock updated",
                "zone_created": "Zone created",
                "maintenance": "Maintenance completed",
                "user_login": "User logged in",
                "user_signup": "User signed up",
                "email_verified": "Email verified",
            }
            return mapping.get(e.event_type, e.event_type.replace("_", " ").title())

        data = [
            {
                "id": str(ev.id),
                "action": to_action(ev),
                "time": ev.occurred_at.isoformat(),
                "user": str(ev.user_id) if ev.user_id else "System",
                "type": ev.event_type.split("_")[0] if ev.event_type else "event",
            }
            for ev in events
        ]
        return ResponseModel(success=True, data={"activities": data})
    except Exception as e:
        return ResponseModel(success=False, error=str(e))


@router.get("/users", response_model=ResponseModel)
async def list_users(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Very protected: list all users (admin only)."""
    try:
        users = db.exec(select(User)).all()
        data = [
            {
                "id": str(u.id),
                "email": u.email,
                "name": u.name,
                "phone": u.phone,
                "verified_status": u.verified_status,
                "email_verified": bool(u.email_verified),
                "eco_points": int(u.eco_points or 0),
                "created_at": u.created_at.isoformat() if getattr(u, "created_at", None) else None,
            }
            for u in users
        ]
        return ResponseModel(success=True, data={"users": data})
    except Exception as e:
        return ResponseModel(success=False, error=str(e))


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


@router.patch("/users/{user_id}/role", response_model=ResponseModel)
async def update_user_role(
    user_id: str,
    role: UserRole,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Promote/demote a user's role (admin/staff/user)."""
    user = db.exec(select(User).where(User.id == user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    user.role = role
    db.add(user)
    db.commit()
    return ResponseModel(success=True, message="User role updated", data={"user_id": user_id, "role": role})
