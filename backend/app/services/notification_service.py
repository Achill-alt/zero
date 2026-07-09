"""Notification service — create, list, mark-read, and unread-count operations."""
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.notification import Notification
from app.models.user import User


def create_notification(
    db: Session,
    user_id: int,
    type_: str,
    title: str,
    content: str = None,
    related_id: int = None,
) -> Notification:
    """Create a notification record and return it."""
    notif = Notification(
        user_id=user_id,
        type=type_,
        title=title,
        content=content,
        related_id=related_id,
    )
    db.add(notif)
    db.commit()
    db.refresh(notif)
    return notif


def list_notifications(
    db: Session,
    user_id: int,
    page: int = 1,
    page_size: int = 20,
):
    """List notifications for a user, unread-first then by time desc."""
    base = (
        db.query(Notification)
        .filter(Notification.user_id == user_id)
    )
    total = base.count()
    items = (
        base
        .order_by(Notification.is_read.asc(), Notification.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return {"items": items, "total": total, "page": page, "page_size": page_size}


def get_unread_count(db: Session, user_id: int) -> int:
    return (
        db.query(Notification)
        .filter(Notification.user_id == user_id, Notification.is_read == False)
        .count()
    )


def mark_as_read(db: Session, notification_id: int, user_id: int) -> Notification:
    notif = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notif:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="通知不存在")
    if notif.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权操作此通知")
    notif.is_read = True
    db.commit()
    db.refresh(notif)
    return notif


def mark_all_as_read(db: Session, user_id: int) -> int:
    """Mark all unread notifications as read for the user. Returns count updated."""
    count = (
        db.query(Notification)
        .filter(Notification.user_id == user_id, Notification.is_read == False)
        .update({"is_read": True})
    )
    db.commit()
    return count


def _get_users_by_approver_role(db: Session, approver_role: str):
    """Get active users with the given approver_role."""
    return (
        db.query(User)
        .filter(User.approver_role == approver_role, User.is_active == True)
        .all()
    )


def notify_approver_role(
    db: Session,
    approver_role: str,
    title: str,
    content: str,
    related_id: int = None,
):
    """Create notifications for all active users with a given approver_role."""
    users = _get_users_by_approver_role(db, approver_role)
    for user in users:
        create_notification(db, user.id, "approval_new", title, content, related_id)


def notify_user(
    db: Session,
    user_id: int,
    type_: str,
    title: str,
    content: str,
    related_id: int = None,
):
    """Create a single notification for a specific user."""
    create_notification(db, user_id, type_, title, content, related_id)
