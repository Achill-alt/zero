from pydantic import BaseModel
from typing import Optional


class UserUpdate(BaseModel):
    role: Optional[str] = None
    approver_role: Optional[str] = None
    department: Optional[str] = None
    display_name: Optional[str] = None
    is_active: Optional[bool] = None
