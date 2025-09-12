from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from app.database import get_db
from app.models.user import User
from app.models.zone import Zone
from app.auth import get_current_admin_user
from app.schemas.common import ResponseModel

router = APIRouter()


@router.get("/", response_model=ResponseModel)
async def get_zones(
    since: str = None,
    db: Session = Depends(get_db)
):
    """Get zones with GeoJSON format"""
    zones = db.exec(select(Zone)).all()
    
    return ResponseModel(
        success=True,
        data={"zones": [
            {
                "id": str(zone.id),
                "kind": zone.kind,
                "polygon": {"type": "Polygon", "coordinates": []},  # TODO: Convert PostGIS to GeoJSON
                "label": zone.label
            } for zone in zones
        ]}
    )


@router.post("/admin", response_model=ResponseModel)
async def create_zone(
    kind: str,
    polygon_coords: list,
    label: str = None,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Create or update a zone (admin only)"""
    # TODO: Implement PostGIS polygon creation
    zone = Zone(
        kind=kind,
        polygon=b"",  # TODO: Convert coordinates to PostGIS geometry
        label=label,
        created_by=current_user.id
    )
    
    db.add(zone)
    db.commit()
    
    return ResponseModel(
        success=True,
        message="Zone created successfully"
    )
