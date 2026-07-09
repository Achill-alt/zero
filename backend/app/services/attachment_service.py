import os
import uuid
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.orm import Session
from app.config import settings
from app.models.attachment import ContractAttachment
from app.models.contract import Contract

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "image/png",
    "image/jpeg",
    "image/gif",
    "text/plain",
}

# Map MIME types to safe extensions (used when browser gives unreliable content_type)
ALLOWED_EXTENSIONS = {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".png", ".jpg", ".jpeg", ".gif", ".txt"}


def _validate_file(file: UploadFile):
    """Validate file type and size before saving."""
    # Validate extension
    if file.filename:
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的文件类型: {ext}。支持的类型: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
            )

    # Validate MIME type
    if file.content_type and file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的文件类型: {file.content_type}",
        )


def save_attachment(db: Session, contract_id: int, file: UploadFile, user_id: int) -> ContractAttachment:
    """Save an uploaded file to disk and create a DB record."""
    # Verify contract exists
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="合同不存在")

    _validate_file(file)

    # Read file content
    content = file.file.read()
    if len(content) > settings.max_upload_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"文件大小超过限制 ({settings.max_upload_size // (1024 * 1024)}MB)",
        )

    # Determine extension
    ext = os.path.splitext(file.filename)[1].lower() if file.filename else ".bin"

    # Build directory and filename
    dir_path = os.path.join(settings.upload_dir, str(contract_id))
    os.makedirs(dir_path, exist_ok=True)

    stored_name = f"{uuid.uuid4().hex}{ext}"
    stored_path = os.path.join(dir_path, stored_name)

    # Write to disk
    with open(stored_path, "wb") as f:
        f.write(content)

    # Create DB record
    attachment = ContractAttachment(
        contract_id=contract_id,
        filename=file.filename or stored_name,
        stored_path=stored_path,
        file_size=len(content),
        mime_type=file.content_type or "application/octet-stream",
        uploaded_by=user_id,
    )
    db.add(attachment)
    db.commit()
    db.refresh(attachment)
    return attachment


def list_attachments(db: Session, contract_id: int) -> list[ContractAttachment]:
    """Return all attachments for a contract."""
    return (
        db.query(ContractAttachment)
        .filter(ContractAttachment.contract_id == contract_id)
        .order_by(ContractAttachment.created_at.desc())
        .all()
    )


def get_attachment(db: Session, attachment_id: int) -> ContractAttachment:
    """Get a single attachment by ID."""
    attachment = db.query(ContractAttachment).filter(ContractAttachment.id == attachment_id).first()
    if not attachment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="附件不存在")
    return attachment


def delete_attachment(db: Session, attachment_id: int, user_id: int):
    """Delete an attachment record and its file from disk."""
    attachment = get_attachment(db, attachment_id)

    # Remove from disk (best-effort, don't fail if file already gone)
    try:
        if os.path.exists(attachment.stored_path):
            os.remove(attachment.stored_path)
    except OSError:
        pass

    db.delete(attachment)
    db.commit()
