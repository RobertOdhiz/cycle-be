# app/models/notification.py
from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from uuid import uuid4

from sqlmodel import SQLModel, Field, Column
from sqlalchemy import Enum as SQLEnum, JSON

class NotificationChannel(str, Enum):
    push = "push"
    sms = "sms"
    email = "email"
    in_app = "in-app"

class NotificationStatus(str, Enum):
    pending = "pending"
    sent = "sent"
    failed = "failed"

class Notification(SQLModel, table=True):
    __tablename__ = "notifications"

    id: Optional[str] = Field(default_factory=lambda: str(uuid4()), primary_key=True, nullable=False)
    user_id: str = Field(foreign_key="users.id", nullable=False)

    channel: NotificationChannel = Field(
        sa_column=Column(
            SQLEnum(NotificationChannel, name="notificationchannel_enum"),
            nullable=False
        ),
        default=NotificationChannel.push
    )

    title: Optional[str] = None
    body: Optional[str] = None

    data: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))

    status: NotificationStatus = Field(
        sa_column=Column(
            SQLEnum(NotificationStatus, name="notificationstatus_enum"),
            nullable=False,
            server_default=NotificationStatus.pending.value
        ),
        default=NotificationStatus.pending
    )

    sent_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
