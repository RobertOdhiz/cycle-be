from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from app.auth.dependencies import get_current_user
from sqlmodel import Session, select
from app.database import get_db
from app.models.user import User
from app.models.notification import Notification
from app.auth import get_current_admin_user
from app.schemas.common import ResponseModel
from app.worker.tasks import send_push_notification

router = APIRouter()


@router.post("/send", response_model=ResponseModel)
async def send_notification(
    user_ids: list[str] | None = None,
    channel: str = "push",
    title: str = "",
    body: str = "",
    data: dict | None = None,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = None
):
    """Send notification to users (admin only)"""
    if not title or not body:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Title and body are required")

    valid_channels = {"push", "email", "sms"}
    if channel not in valid_channels:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid channel")

    # If no recipients provided, send to all users
    if not user_ids or len(user_ids) == 0:
        all_ids = db.exec(select(User.id)).all()
        user_ids = [str(u[0] if isinstance(u, tuple) else u) for u in all_ids]

    # Create notification records
    notifications = []
    for user_id in user_ids:
        notification = Notification(
            user_id=user_id,
            channel=channel,
            title=title,
            body=body,
            data=data or {}
        )
        notifications.append(notification)
    
    db.add_all(notifications)
    db.commit()
    
    # Enqueue background task for sending
    if background_tasks and channel == "push":
        background_tasks.add_task(send_push_notification.delay, user_ids, title, body, data or {})
    
    return ResponseModel(
        success=True,
        message=f"Notifications queued for {len(user_ids)} users"
    )


@router.get("/", response_model=ResponseModel)
async def get_notifications(
    since: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get notifications for current user"""
    query = select(Notification).where(Notification.user_id == current_user.id)
    
    if since:
        # TODO: Add since filtering
        pass
    
    notifications = db.exec(query).all()
    
    return ResponseModel(
        success=True,
        data={"notifications": [
            {
                "id": str(n.id),
                "channel": n.channel,
                "title": n.title,
                "body": n.body,
                "status": n.status,
                "created_at": n.created_at.isoformat()
            } for n in notifications
        ]}
    )
