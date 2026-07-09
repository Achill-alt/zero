from pydantic import BaseModel, ConfigDict
from typing import Optional


class NotificationResponse(BaseModel):
    id: int
    user_id: int
    type: str
    title: str
    content: Optional[str] = None
    is_read: bool
    related_id: Optional[int] = None
    created_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
