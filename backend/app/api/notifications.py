"""Notification REST endpoints."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.user import User
from app.services import notification_service
from app.utils.serializers import notification_to_dict

router = APIRouter()


@router.get("/notifications", response_model=dict)
def list_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List notifications for the current user (unread first, then by time desc)."""
    result = notification_service.list_notifications(db, current_user.id, page, page_size)
    return {
        "data": {
            "items": [notification_to_dict(n) for n in result["items"]],
            "total": result["total"],
            "page": result["page"],
            "page_size": result["page_size"],
        },
        "message": "success",
    }


@router.get("/notifications/unread-count", response_model=dict)
def unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the count of unread notifications."""
    count = notification_service.get_unread_count(db, current_user.id)
    return {"data": {"count": count}, "message": "success"}


@router.put("/notifications/{notification_id}/read", response_model=dict)
def mark_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark a single notification as read."""
    notification_service.mark_as_read(db, notification_id, current_user.id)
    return {"data": None, "message": "已读"}


@router.put("/notifications/read-all", response_model=dict)
def mark_all_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark all notifications as read."""
    count = notification_service.mark_all_as_read(db, current_user.id)
    return {"data": {"updated": count}, "message": f"已将 {count} 条通知标记为已读"}
