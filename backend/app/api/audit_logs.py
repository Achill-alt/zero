from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.audit_service import get_logs
from app.middleware.auth import get_current_user, require_role

router = APIRouter()


@router.get("", response_model=dict)
def list_logs(
    user_id: int = Query(None),
    action: str = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    result = get_logs(db, user_id, action, page, page_size)
    items = []
    for log in result["items"]:
        items.append({
            "id": log.id,
            "user_id": log.user_id,
            "action": log.action,
            "target_type": log.target_type,
            "target_id": log.target_id,
            "detail": log.detail,
            "created_at": str(log.created_at) if log.created_at else None,
        })
    return {"data": {"items": items, "total": result["total"], "page": page, "page_size": page_size}, "message": "success"}
