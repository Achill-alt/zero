from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas.user import UserUpdate
from app.services.audit_service import log_action
from app.middleware.auth import get_current_user, require_role
from app.utils.serializers import user_to_dict

router = APIRouter()


@router.get("", response_model=dict)
def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    query = db.query(User)
    total = query.count()
    items = query.order_by(User.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {
        "data": {
            "items": [user_to_dict(u) for u in items],
            "total": total,
            "page": page,
            "page_size": page_size,
        },
        "message": "success",
    }


@router.put("/{user_id}", response_model=dict)
def update_user(
    user_id: int,
    data: UserUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(user, key, value)

    db.commit()
    db.refresh(user)
    log_action(db, current_user.id, "user_update", "user", user_id)
    return {"data": user_to_dict(user), "message": "success"}
