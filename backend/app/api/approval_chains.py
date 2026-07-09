import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.approval import ApprovalChainTemplate
from app.schemas.approval import ApprovalChainCreate, ApprovalChainUpdate
from app.services.audit_service import log_action
from app.middleware.auth import get_current_user, require_role
from app.utils.serializers import chain_to_dict

router = APIRouter()


@router.get("", response_model=dict)
def list_chains(
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    items = db.query(ApprovalChainTemplate).order_by(ApprovalChainTemplate.priority.desc()).all()
    return {
        "data": [chain_to_dict(c) for c in items],
        "message": "success",
    }


@router.post("", response_model=dict)
def create_chain(
    data: ApprovalChainCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    chain = ApprovalChainTemplate(
        name=data.name,
        conditions=json.dumps(data.conditions),
        steps=json.dumps(data.steps),
        priority=data.priority,
        is_active=data.is_active,
    )
    db.add(chain)
    db.commit()
    db.refresh(chain)
    log_action(db, current_user.id, "approval_chain_create", "approval_chain_template", chain.id,
               {"name": chain.name})
    return {"data": chain_to_dict(chain), "message": "success"}


@router.put("/{chain_id}", response_model=dict)
def update_chain(
    chain_id: int,
    data: ApprovalChainUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    chain = db.query(ApprovalChainTemplate).filter(ApprovalChainTemplate.id == chain_id).first()
    if not chain:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="审批链模板不存在")

    update_data = data.model_dump(exclude_unset=True)
    if "conditions" in update_data:
        update_data["conditions"] = json.dumps(update_data["conditions"])
    if "steps" in update_data:
        update_data["steps"] = json.dumps(update_data["steps"])

    for key, value in update_data.items():
        setattr(chain, key, value)

    db.commit()
    db.refresh(chain)
    log_action(db, current_user.id, "approval_chain_update", "approval_chain_template", chain_id,
               {"name": chain.name})
    return {"data": chain_to_dict(chain), "message": "success"}


@router.delete("/{chain_id}", response_model=dict)
def delete_chain(
    chain_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    chain = db.query(ApprovalChainTemplate).filter(ApprovalChainTemplate.id == chain_id).first()
    if not chain:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="审批链模板不存在")

    # Check if any in-progress instances reference this template
    from app.models.approval import ApprovalInstance
    active = db.query(ApprovalInstance).filter(
        ApprovalInstance.template_id == chain_id,
        ApprovalInstance.status == "in_progress",
    ).first()
    if active:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="存在进行中的审批实例引用此模板，无法删除")

    db.delete(chain)
    db.commit()
    return {"message": "已删除"}
