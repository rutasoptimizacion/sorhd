"""
Notification API Endpoints

Provides endpoints for managing notifications and device tokens.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.models.user import User, UserRole
from app.models.notification import Notification, NotificationType
from app.schemas.common import PaginatedResponse
from app.services.notification_service import (
    NotificationService,
    NotificationPayload,
    NotificationTemplates
)
from pydantic import BaseModel, Field

router = APIRouter()


# Request/Response Schemas

class DeviceTokenRequest(BaseModel):
    """Request to register device token"""
    device_token: str = Field(..., description="FCM or APNS device token")


class DeviceTokenResponse(BaseModel):
    """Response after registering device token"""
    success: bool
    message: str


class SendNotificationRequest(BaseModel):
    """Request to send notification (admin only)"""
    user_ids: List[int] = Field(..., description="Target user IDs")
    type: NotificationType = Field(..., description="Notification type")
    title: str = Field(..., min_length=1, max_length=100)
    body: str = Field(..., min_length=1, max_length=500)
    data: Optional[dict] = Field(None, description="Additional data payload")


class NotificationResponse(BaseModel):
    """Notification response schema"""
    id: int
    user_id: int
    type: str
    title: str
    message: str
    data: dict
    status: str
    delivery_channel: Optional[str]
    read_at: Optional[str]
    sent_at: Optional[str]
    created_at: str

    class Config:
        from_attributes = True


class MarkReadRequest(BaseModel):
    """Request to mark notification as read"""
    notification_ids: List[int] = Field(..., description="Notification IDs to mark as read")


# Endpoints

@router.post("/device-token", response_model=DeviceTokenResponse)
async def register_device_token(
    request: DeviceTokenRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Register device token for push notifications.

    Clinical team and patients can register their device tokens
    to receive push notifications.
    """
    service = NotificationService(db=db)

    success = await service.register_device_token(
        user_id=current_user.id,
        device_token=request.device_token
    )

    if success:
        return DeviceTokenResponse(
            success=True,
            message="Device token registered successfully"
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to register device token"
        )


@router.get("/", response_model=PaginatedResponse[NotificationResponse])
async def get_notifications(
    unread_only: bool = Query(False, description="Filter unread notifications only"),
    limit: int = Query(50, ge=1, le=100, description="Number of notifications per page"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get notifications for the current user.

    Returns paginated list of notifications, optionally filtered to unread only.
    """
    service = NotificationService(db=db)

    notifications = await service.get_user_notifications(
        user_id=current_user.id,
        unread_only=unread_only,
        limit=limit,
        offset=offset
    )

    # Convert to response models
    notification_responses = [
        NotificationResponse(
            id=n.id,
            user_id=n.user_id,
            type=n.type.value,
            title=n.title,
            message=n.message,
            data=n.data,
            status=n.status.value,
            delivery_channel=n.delivery_channel,
            read_at=n.read_at.isoformat() if n.read_at else None,
            sent_at=n.sent_at.isoformat() if n.sent_at else None,
            created_at=n.created_at.isoformat()
        )
        for n in notifications
    ]

    return PaginatedResponse(
        items=notification_responses,
        total=len(notification_responses),
        limit=limit,
        offset=offset
    )


@router.patch("/{notification_id}/read", response_model=NotificationResponse)
async def mark_notification_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Mark a notification as read.

    Users can only mark their own notifications as read.
    """
    service = NotificationService(db=db)

    notification = await service.mark_as_read(
        notification_id=notification_id,
        user_id=current_user.id
    )

    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )

    return NotificationResponse(
        id=notification.id,
        user_id=notification.user_id,
        type=notification.type.value,
        title=notification.title,
        message=notification.message,
        data=notification.data,
        status=notification.status.value,
        delivery_channel=notification.delivery_channel,
        read_at=notification.read_at.isoformat() if notification.read_at else None,
        sent_at=notification.sent_at.isoformat() if notification.sent_at else None,
        created_at=notification.created_at.isoformat()
    )


@router.post("/mark-read-batch")
async def mark_notifications_read_batch(
    request: MarkReadRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Mark multiple notifications as read in batch.
    """
    service = NotificationService(db=db)

    marked_count = 0
    for notification_id in request.notification_ids:
        notification = await service.mark_as_read(
            notification_id=notification_id,
            user_id=current_user.id
        )
        if notification:
            marked_count += 1

    return {
        "success": True,
        "marked_count": marked_count,
        "total_requested": len(request.notification_ids)
    }


@router.post("/send", dependencies=[Depends(require_role(UserRole.ADMIN))])
async def send_notification(
    request: SendNotificationRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Send notification to users (Admin only).

    Allows administrators to manually send notifications to users.
    """
    service = NotificationService(db=db)

    payload = NotificationPayload(
        title=request.title,
        body=request.body,
        data=request.data
    )

    notifications = await service.send_bulk_notification(
        user_ids=request.user_ids,
        notification_type=request.type,
        payload=payload
    )

    success_count = sum(1 for n in notifications if n.status.value == "sent")

    return {
        "success": True,
        "total_sent": len(notifications),
        "successful": success_count,
        "failed": len(notifications) - success_count,
        "notification_ids": [n.id for n in notifications]
    }


@router.get("/unread-count")
async def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get count of unread notifications for current user.

    Useful for displaying notification badge counts.
    """
    service = NotificationService(db=db)

    notifications = await service.get_user_notifications(
        user_id=current_user.id,
        unread_only=True,
        limit=1000  # High limit to count all
    )

    return {
        "unread_count": len(notifications)
    }


@router.delete("/{notification_id}", dependencies=[Depends(require_role(UserRole.ADMIN))])
async def delete_notification(
    notification_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a notification (Admin only).

    Useful for removing test notifications or cleaning up old data.
    """
    from sqlalchemy import delete as sql_delete
    from app.models.notification import Notification

    result = await db.execute(
        sql_delete(Notification).where(Notification.id == notification_id)
    )
    await db.commit()

    if result.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )

    return {
        "success": True,
        "message": f"Notification {notification_id} deleted"
    }
