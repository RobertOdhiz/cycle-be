from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from app.database import get_db
from app.models.user import User
from app.models.bike import Bike
from app.models.rental import Rental
from app.auth import get_current_user
from app.schemas.rental import (
    RideStartRequest,
    RideStartResponse,
    RideEndRequest,
    RideEndResponse
)
from app.schemas.common import ResponseModel
from app.services.events import track_event
from decimal import Decimal
from datetime import datetime

router = APIRouter()


@router.post("/start", response_model=ResponseModel[RideStartResponse])
async def start_ride(
    request: RideStartRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Start a bike ride"""
    # Check idempotency
    if request.client_rental_id:
        existing_rental = db.exec(
            select(Rental).where(
                Rental.client_rental_id == request.client_rental_id,
                Rental.user_id == request.user_id
            )
        ).first()
        if existing_rental:
            return ResponseModel(
                success=True,
                data=RideStartResponse(
                    rental_id=existing_rental.id,
                    server_start_at=existing_rental.start_at
                )
            )
    
    # Get bike and check availability
    bike = db.exec(select(Bike).where(Bike.id == request.bike_id)).first()
    if not bike:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bike not found"
        )
    
    if bike.status != "available":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bike not available"
        )
    
    # Create rental
    rental = Rental(
        client_rental_id=request.client_rental_id,
        bike_id=request.bike_id,
        user_id=request.user_id,
        start_at=request.start_at,
        minute_rate_snapshot=request.minute_rate_snapshot
    )
    
    # Update bike status
    bike.status = "rented"
    
    db.add(rental)
    db.add(bike)
    db.commit()
    db.refresh(rental)
    
    # Track event
    track_event(
        db,
        user_id=current_user.id,
        bike_id=bike.id,
        event_type="ride_start"
    )
    
    return ResponseModel(
        success=True,
        data=RideStartResponse(
            rental_id=rental.id,
            server_start_at=rental.start_at
        )
    )


@router.post("/end", response_model=ResponseModel[RideEndResponse])
async def end_ride(
    request: RideEndRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """End a bike ride"""
    # Find rental
    if request.rental_id:
        rental = db.exec(select(Rental).where(Rental.id == request.rental_id)).first()
    elif request.client_rental_id:
        rental = db.exec(
            select(Rental).where(
                Rental.client_rental_id == request.client_rental_id,
                Rental.user_id == current_user.id
            )
        ).first()
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either rental_id or client_rental_id required"
        )
    
    if not rental:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rental not found"
        )
    
    if rental.status != "open":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rental already ended"
        )
    
    # Calculate amount
    amount = rental.minute_rate_snapshot * Decimal(request.minutes_client)
    amount = round(amount, 2)
    
    # Update rental
    rental.end_at = request.end_at
    rental.minutes_client = request.minutes_client
    rental.amount = amount
    rental.status = "closed"
    rental.path_sample = request.path_sample
    
    # Update bike status
    bike = db.exec(select(Bike).where(Bike.id == rental.bike_id)).first()
    if bike:
        bike.status = "available"
        db.add(bike)
    
    db.add(rental)
    db.commit()
    
    # Track event
    track_event(
        db,
        user_id=current_user.id,
        bike_id=rental.bike_id,
        event_type="ride_end",
        properties={"minutes": request.minutes_client, "amount": float(amount)}
    )
    
    return ResponseModel(
        success=True,
        data=RideEndResponse(
            rental_id=rental.id,
            amount=amount,
            minutes=request.minutes_client,
            payment_instructions="Please complete payment via M-Pesa or other methods"
        )
    )
