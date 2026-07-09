import json
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.approval import ApprovalInstance, ApprovalChainTemplate
from app.models.contract import Contract
from app.models.user import User
from app.utils.json_helpers import parse_json_field


def get_pending_approvals(db: Session, user: User, page: int = 1, page_size: int = 20):
    """Get contracts pending approval for the current user's approver_role, paginated."""
    if not user.approver_role:
        return {"items": [], "total": 0, "page": page, "page_size": page_size}

    instances = (
        db.query(ApprovalInstance)
        .filter(ApprovalInstance.status == "in_progress")
        .all()
    )

    result = []
    for inst in instances:
        template = db.query(ApprovalChainTemplate).filter(ApprovalChainTemplate.id == inst.template_id).first()
        if not template:
            continue

        steps = parse_json_field(template.steps)
        if inst.current_step_index >= len(steps):
            continue

        current_step = steps[inst.current_step_index]
        if current_step.get("role") == user.approver_role:
            contract = db.query(Contract).filter(Contract.id == inst.contract_id).first()
            if contract:
                result.append({
                    "instance": inst,
                    "contract": contract,
                    "current_step": current_step,
                    "template_name": template.name,
                })

    total = len(result)
    start = (page - 1) * page_size
    items = result[start:start + page_size]

    return {"items": items, "total": total, "page": page, "page_size": page_size}


def approve_step(db: Session, instance_id: int, user: User, comment: str = ""):
    instance = db.query(ApprovalInstance).filter(ApprovalInstance.id == instance_id).first()
    if not instance:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="审批实例不存在")
    if instance.status != "in_progress":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="该审批已结束")

    template = db.query(ApprovalChainTemplate).filter(ApprovalChainTemplate.id == instance.template_id).first()
    steps = parse_json_field(template.steps)
    if instance.current_step_index >= len(steps):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="审批已完成")

    current_step = steps[instance.current_step_index]
    if current_step.get("role") != user.approver_role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="您不是当前步骤的审批人")

    # Record step result
    step_results = parse_json_field(instance.step_results)
    step_results.append({
        "step_index": instance.current_step_index,
        "step_name": current_step.get("name", ""),
        "user_id": user.id,
        "user_name": user.display_name,
        "action": "approve",
        "comment": comment,
        "acted_at": datetime.now(timezone.utc).isoformat(),
    })

    # Move to next step or complete
    if instance.current_step_index + 1 >= len(steps):
        instance.status = "approved"
        instance.step_results = json.dumps(step_results)

        # Update contract status
        contract = db.query(Contract).filter(Contract.id == instance.contract_id).first()
        if contract:
            contract.status = "approved"

            # Notify creator: contract approved
            from app.services.notification_service import notify_user
            notify_user(
                db,
                user_id=contract.creator_id,
                type_="approval_result",
                title="审批已通过",
                content=f"合同「{contract.title}」已通过所有审批",
                related_id=contract.id,
            )
    else:
        instance.current_step_index += 1
        instance.step_results = json.dumps(step_results)

        # Notify the next-step approver
        next_step = steps[instance.current_step_index]
        from app.services.notification_service import notify_approver_role
        notify_approver_role(
            db,
            approver_role=next_step.get("role", ""),
            title="新的审批任务",
            content=f"合同「{instance.contract_id}」已通过前序审批，等待您处理",
            related_id=instance.contract_id,
        )

    db.commit()
    db.refresh(instance)
    return instance


def reject_step(db: Session, instance_id: int, user: User, comment: str):
    instance = db.query(ApprovalInstance).filter(ApprovalInstance.id == instance_id).first()
    if not instance:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="审批实例不存在")
    if instance.status != "in_progress":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="该审批已结束")

    template = db.query(ApprovalChainTemplate).filter(ApprovalChainTemplate.id == instance.template_id).first()
    steps = parse_json_field(template.steps)

    current_step = steps[instance.current_step_index]
    if current_step.get("role") != user.approver_role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="您不是当前步骤的审批人")

    step_results = parse_json_field(instance.step_results)
    step_results.append({
        "step_index": instance.current_step_index,
        "step_name": current_step.get("name", ""),
        "user_id": user.id,
        "user_name": user.display_name,
        "action": "reject",
        "comment": comment,
        "acted_at": datetime.now(timezone.utc).isoformat(),
    })

    instance.status = "rejected"
    instance.step_results = json.dumps(step_results)

    # Return contract to draft
    contract = db.query(Contract).filter(Contract.id == instance.contract_id).first()
    if contract:
        contract.status = "draft"

        # Notify creator: contract rejected
        from app.services.notification_service import notify_user
        notify_user(
            db,
            user_id=contract.creator_id,
            type_="approval_result",
            title="审批已驳回",
            content=f"合同「{contract.title}」已被 {current_step.get('name', '')}（{user.display_name}）驳回",
            related_id=contract.id,
        )

    db.commit()
    db.refresh(instance)
    return instance


def withdraw_approval(db: Session, instance_id: int, user_id: int):
    instance = db.query(ApprovalInstance).filter(ApprovalInstance.id == instance_id).first()
    if not instance:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="审批实例不存在")
    if instance.status != "in_progress":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="只有审批中的实例可以撤回")

    contract = db.query(Contract).filter(Contract.id == instance.contract_id).first()
    if not contract or contract.creator_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="只有合同经办人可以撤回")

    instance.status = "withdrawn"
    contract.status = "draft"
    db.commit()
    return instance
