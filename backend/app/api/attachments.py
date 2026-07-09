from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.middleware.auth import get_current_user, require_role
from app.services.attachment_service import (
    save_attachment,
    list_attachments,
    get_attachment,
    delete_attachment,
)
from app.utils.serializers import attachment_to_dict

router = APIRouter()


@router.post("/contracts/{contract_id}/attachments", response_model=dict)
async def upload(
    contract_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(require_role("handler", "admin")),
):
    attachment = save_attachment(db, contract_id, file, current_user.id)
    return {"data": attachment_to_dict(attachment), "message": "上传成功"}


@router.get("/contracts/{contract_id}/attachments", response_model=dict)
def list_attachment_list(
    contract_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    attachments = list_attachments(db, contract_id)
    return {"data": [attachment_to_dict(a) for a in attachments], "message": "success"}


@router.get("/attachments/{attachment_id}/download")
def download(
    attachment_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    attachment = get_attachment(db, attachment_id)
    if not hasattr(attachment, "stored_path") or not attachment.stored_path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="附件文件不存在")
    return FileResponse(
        path=attachment.stored_path,
        filename=attachment.filename,
        media_type=attachment.mime_type or "application/octet-stream",
    )


@router.delete("/attachments/{attachment_id}", response_model=dict)
def delete(
    attachment_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("handler", "admin")),
):
    delete_attachment(db, attachment_id, current_user.id)
    return {"data": None, "message": "删除成功"}
