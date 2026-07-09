from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.approval import ApprovalAction
from app.services.approval_service import get_pending_approvals, approve_step, reject_step, withdraw_approval
from app.services.audit_service import log_action
from app.middleware.auth import get_current_user, require_role

router = APIRouter()


@router.get("/pending", response_model=dict)
def pending(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(require_role("approver", "admin")),
):
    result = get_pending_approvals(db, current_user, page, page_size)
    items = []
    for item in result["items"]:
        items.append({
            "instance_id": item["instance"].id,
            "contract_id": item["contract"].id,
            "contract_title": item["contract"].title,
            "contract_type": item["contract"].contract_type,
            "amount": item["contract"].amount,
            "creator_id": item["contract"].creator_id,
            "current_step": item["current_step"],
            "template_name": item["template_name"],
            "current_step_index": item["instance"].current_step_index,
            "status": item["instance"].status,
            "created_at": str(item["instance"].created_at) if item["instance"].created_at else None,
        })
    return {
        "data": {
            "items": items,
            "total": result["total"],
            "page": result["page"],
            "page_size": result["page_size"],
        },
        "message": "success",
    }


@router.post("/{instance_id}/approve", response_model=dict)
def approve(
    instance_id: int,
    action: ApprovalAction,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("approver", "admin")),
):
    instance = approve_step(db, instance_id, current_user, action.comment)
    log_action(db, current_user.id, "contract_approve", "approval_instance", instance_id,
               {"comment": action.comment, "new_status": instance.status})
    return {"data": {"status": instance.status, "current_step_index": instance.current_step_index}, "message": "审批通过"}


@router.post("/{instance_id}/reject", response_model=dict)
def reject(
    instance_id: int,
    action: ApprovalAction,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("approver", "admin")),
):
    instance = reject_step(db, instance_id, current_user, action.comment)
    log_action(db, current_user.id, "contract_reject", "approval_instance", instance_id,
               {"comment": action.comment})
    return {"data": {"status": instance.status}, "message": "已驳回"}


@router.post("/{instance_id}/withdraw", response_model=dict)
def withdraw(
    instance_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("handler", "admin")),
):
    instance = withdraw_approval(db, instance_id, current_user.id)
    log_action(db, current_user.id, "contract_withdraw", "approval_instance", instance_id)
    return {"data": {"status": instance.status}, "message": "已撤回"}
