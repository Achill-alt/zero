import json
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException, status
from app.models.contract import Contract, ContractTemplate
from app.models.approval import ApprovalChainTemplate, ApprovalInstance
from app.schemas.contract import ContractCreate, ContractUpdate
from app.utils.json_helpers import parse_json_field
from app.services.search_service import reindex_contract

VALID_TYPES = ["purchase", "sales", "service", "lease", "other"]
VALID_STATUSES = ["draft", "pending_approval", "approved", "archived", "voided"]
STATUS_TRANSITIONS = {
    "draft": ["pending_approval", "voided"],
    "pending_approval": ["draft", "approved", "voided"],
    "approved": ["archived"],
}


def check_status_transition(current: str, target: str) -> bool:
    return target in STATUS_TRANSITIONS.get(current, [])


def create_contract(db: Session, data: ContractCreate, creator_id: int) -> Contract:
    if data.contract_type not in VALID_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"无效的合同类型: {data.contract_type}")

    contract = Contract(
        title=data.title,
        content=data.content,
        contract_type=data.contract_type,
        amount=data.amount,
        party_a=data.party_a,
        party_b=data.party_b,
        start_date=data.start_date,
        end_date=data.end_date,
        status="draft",
        creator_id=creator_id,
        template_id=data.template_id,
    )
    db.add(contract)
    db.commit()
    db.refresh(contract)
    reindex_contract(db, contract.id, contract.title, contract.content)
    return contract


def update_contract(db: Session, contract_id: int, data: ContractUpdate, user_id: int) -> Contract:
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="合同不存在")
    if contract.status not in ("draft", "voided"):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="当前状态不允许编辑")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(contract, key, value)

    db.commit()
    db.refresh(contract)
    reindex_contract(db, contract.id, contract.title, contract.content)
    return contract


def submit_contract(db: Session, contract_id: int, user_id: int) -> dict:
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="合同不存在")
    if contract.status != "draft":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="只有草稿状态的合同可以提交审批")

    # Match approval chain
    template = match_approval_chain(db, contract)
    if not template:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="未找到匹配的审批链模板")

    steps = parse_json_field(template.steps)

    instance = ApprovalInstance(
        contract_id=contract.id,
        template_id=template.id,
        current_step_index=0,
        status="in_progress",
        step_results=json.dumps([]),
    )
    db.add(instance)
    contract.status = "pending_approval"
    db.commit()
    db.refresh(instance)

    # Notify the first-step approver
    from app.services.notification_service import notify_approver_role
    first_step = steps[0]
    notify_approver_role(
        db,
        approver_role=first_step.get("role", ""),
        title="新的审批任务",
        content=f"合同「{contract.title}」已提交审批，等待您处理",
        related_id=contract.id,
    )

    return {
        "instance_id": instance.id,
        "template_name": template.name,
        "total_steps": len(steps),
        "current_step_index": 0,
        "status": instance.status,
    }


def match_approval_chain(db: Session, contract: Contract):
    """Match the first active approval chain template that satisfies contract conditions."""
    templates = (
        db.query(ApprovalChainTemplate)
        .filter(ApprovalChainTemplate.is_active == True)
        .order_by(ApprovalChainTemplate.priority.desc(), ApprovalChainTemplate.created_at.asc())
        .all()
    )

    for tpl in templates:
        conditions = parse_json_field(tpl.conditions)
        if _check_conditions(conditions, contract):
            return tpl
    return None


def _check_conditions(conditions: dict, contract: Contract) -> bool:
    """Check if contract satisfies all conditions."""
    if not conditions:
        return True

    allowed_types = conditions.get("contract_type")
    if allowed_types and contract.contract_type not in allowed_types:
        return False

    amount_min = conditions.get("amount_min")
    if amount_min is not None and (contract.amount is None or contract.amount < amount_min):
        return False

    amount_max = conditions.get("amount_max")
    if amount_max is not None and (contract.amount is None or contract.amount > amount_max):
        return False

    return True


def get_expiring_contracts(db: Session, days: int = 30, page: int = 1, page_size: int = 20, upcoming_only: bool = False):
    """Return contracts expiring within `days`, computed in SQL via julianday().

    When `upcoming_only` is True, excludes already-expired contracts (days_left < 0).
    """
    days_left_expr = (
        func.julianday(Contract.end_date) - func.julianday("now")
    ).label("days_left")

    base = (
        db.query(Contract, days_left_expr)
        .filter(Contract.status.in_(["approved", "archived", "pending_approval"]))
        .filter(Contract.end_date.isnot(None))
        .filter(
            func.julianday(Contract.end_date) - func.julianday("now") <= days
        )
    )

    if upcoming_only:
        base = base.filter(
            func.julianday(Contract.end_date) - func.julianday("now") >= 0
        )

    total = base.count()

    # Count upcoming (non-expired) contracts separately — always computed
    # so callers can distinguish "即将到期" from "已过期" without a second query.
    upcoming_base = base.filter(
        func.julianday(Contract.end_date) - func.julianday("now") >= 0
    )
    total_upcoming = upcoming_base.count() if not upcoming_only else total

    rows = (
        base.order_by(Contract.end_date.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    items = []
    for contract, days_left_val in rows:
        days_left = int(days_left_val)
        items.append({
            "contract": contract,
            "days_left": days_left,
            "expired": days_left < 0,
        })

    return {"items": items, "total": total, "total_upcoming": total_upcoming, "page": page, "page_size": page_size}


def get_templates(db: Session, page: int = 1, page_size: int = 20):
    query = db.query(ContractTemplate).filter(ContractTemplate.is_active == True)
    total = query.count()
    items = query.order_by(ContractTemplate.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {"items": items, "total": total, "page": page, "page_size": page_size}
