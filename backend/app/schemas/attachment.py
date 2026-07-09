from pydantic import BaseModel, ConfigDict
from typing import Optional


class AttachmentResponse(BaseModel):
    id: int
    contract_id: int
    filename: str
    file_size: int
    mime_type: str
    uploaded_by: int
    created_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
