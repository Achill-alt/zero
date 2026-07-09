from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.contract import ContractTemplate
from app.schemas.contract import ContractTemplateCreate
from app.services.audit_service import log_action
from app.middleware.auth import get_current_user, require_role
from app.utils.serializers import template_to_dict

router = APIRouter()


@router.get("", response_model=dict)
def list_templates(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    query = db.query(ContractTemplate).filter(ContractTemplate.is_active == True)
    total = query.count()
    items = query.order_by(ContractTemplate.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {
        "data": {
            "items": [template_to_dict(t) for t in items],
            "total": total,
            "page": page,
            "page_size": page_size,
        },
        "message": "success",
    }


@router.post("", response_model=dict)
def create_template(
    data: ContractTemplateCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("handler", "admin")),
):
    template = ContractTemplate(
        name=data.name,
        title_template=data.title_template,
        content_template=data.content_template,
        contract_type=data.contract_type,
        creator_id=current_user.id,
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    log_action(db, current_user.id, "template_create", "contract_template", template.id,
               {"name": template.name})
    return {"data": template_to_dict(template), "message": "success"}


@router.put("/{template_id}", response_model=dict)
def update_template(
    template_id: int,
    data: ContractTemplateCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("handler", "admin")),
):
    template = db.query(ContractTemplate).filter(ContractTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="模板不存在")

    template.name = data.name
    template.title_template = data.title_template
    template.content_template = data.content_template
    template.contract_type = data.contract_type
    db.commit()
    db.refresh(template)
    log_action(db, current_user.id, "template_update", "contract_template", template.id,
               {"name": template.name})
    return {"data": template_to_dict(template), "message": "success"}


@router.delete("/{template_id}", response_model=dict)
def delete_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("handler", "admin")),
):
    template = db.query(ContractTemplate).filter(ContractTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="模板不存在")

    db.delete(template)
    db.commit()
    log_action(db, current_user.id, "template_delete", "contract_template", template_id,
               {"name": template.name})
    return {"message": "已删除"}
