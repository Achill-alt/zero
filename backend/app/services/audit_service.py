import json
from sqlalchemy.orm import Session
from app.models.audit_log import AuditLog


def log_action(db: Session, user_id: int, action: str, target_type: str, target_id: int, detail: dict = None):
    log_entry = AuditLog(
        user_id=user_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        detail=json.dumps(detail) if detail else None,
    )
    db.add(log_entry)
    db.commit()
    return log_entry


def get_logs(db: Session, user_id: int = None, action: str = None, page: int = 1, page_size: int = 20):
    query = db.query(AuditLog)
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    if action:
        query = query.filter(AuditLog.action == action)

    total = query.count()
    items = query.order_by(AuditLog.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {"items": items, "total": total, "page": page, "page_size": page_size}
