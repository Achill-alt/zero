from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.contract import Contract
from app.schemas.contract import ContractCreate, ContractUpdate, ContractResponse
from app.services.contract_service import (
    create_contract,
    update_contract,
    submit_contract,
    get_expiring_contracts,
    get_templates,
)
from app.services.audit_service import log_action
from app.middleware.auth import get_current_user, require_role
from app.utils.serializers import contract_to_dict, template_to_dict
from app.utils.json_helpers import parse_json_field

router = APIRouter()


@router.get("", response_model=dict)
def list_contracts(
    status: str = Query(None),
    type: str = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    query = db.query(Contract)
    if status:
        query = query.filter(Contract.status == status)
    if type:
        query = query.filter(Contract.contract_type == type)

    total = query.count()
    items = query.order_by(Contract.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    return {
        "data": {
            "items": [contract_to_dict(c) for c in items],
            "total": total,
            "page": page,
            "page_size": page_size,
        },
        "message": "success",
    }


@router.post("", response_model=dict)
def create(
    data: ContractCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("handler", "admin")),
):
    contract = create_contract(db, data, current_user.id)
    log_action(db, current_user.id, "contract_create", "contract", contract.id,
               {"title": contract.title, "contract_type": contract.contract_type})
    return {"data": contract_to_dict(contract), "message": "success"}


@router.get("/{contract_id}", response_model=dict)
def get_contract(
    contract_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="合同不存在")

    # Get approval history
    from app.models.approval import ApprovalInstance

    instances = db.query(ApprovalInstance).filter(ApprovalInstance.contract_id == contract_id).all()
    approval_history = []
    for inst in instances:
        step_results = parse_json_field(inst.step_results)
        approval_history.append({
            "instance_id": inst.id,
            "template_id": inst.template_id,
            "status": inst.status,
            "current_step_index": inst.current_step_index,
            "step_results": step_results,
            "created_at": str(inst.created_at) if inst.created_at else None,
        })

    return {"data": {**contract_to_dict(contract), "approval_history": approval_history}, "message": "success"}


@router.put("/{contract_id}", response_model=dict)
def update(
    contract_id: int,
    data: ContractUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("handler", "admin")),
):
    contract = update_contract(db, contract_id, data, current_user.id)
    log_action(db, current_user.id, "contract_update", "contract", contract.id, {"title": contract.title})
    return {"data": contract_to_dict(contract), "message": "success"}


@router.post("/{contract_id}/submit", response_model=dict)
def submit(
    contract_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("handler", "admin")),
):
    result = submit_contract(db, contract_id, current_user.id)
    log_action(db, current_user.id, "contract_submit", "contract", contract_id,
               {"template_name": result["template_name"]})
    return {"data": result, "message": "审批已提交"}


@router.post("/{contract_id}/archive", response_model=dict)
def archive(
    contract_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("handler", "admin")),
):
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="合同不存在")
    if contract.status != "approved":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="只有已通过的合同可以归档")

    contract.status = "archived"
    db.commit()
    log_action(db, current_user.id, "contract_archive", "contract", contract_id)
    return {"data": contract_to_dict(contract), "message": "已归档"}


@router.post("/{contract_id}/void", response_model=dict)
def void_contract(
    contract_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("handler", "admin")),
):
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="合同不存在")
    if contract.status != "draft":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="只有草稿状态的合同可以作废")

    contract.status = "voided"
    db.commit()
    log_action(db, current_user.id, "contract_void", "contract", contract_id)
    return {"data": contract_to_dict(contract), "message": "已作废"}


@router.get("/expiring/list", response_model=dict)
def expiring_list(
    days: int = Query(30),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = get_expiring_contracts(db, days, page, page_size)
    items = []
    for item in result["items"]:
        items.append({
            **contract_to_dict(item["contract"]),
            "days_left": item["days_left"],
            "expired": item["expired"],
        })
    return {"data": {"items": items, "total": result["total"], "page": page, "page_size": page_size}, "message": "success"}


@router.get("/templates/all", response_model=dict)
def templates_list(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = get_templates(db, page, page_size)
    items = [template_to_dict(t) for t in result["items"]]
    return {"data": {"items": items, "total": result["total"], "page": page, "page_size": page_size}, "message": "success"}
