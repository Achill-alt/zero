from pydantic import BaseModel, Field, ConfigDict
from typing import Optional


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=100)
    role: str = Field(default="handler")
    approver_role: Optional[str] = None
    department: str = Field(default="")
    display_name: str = Field(default="")


class UserResponse(BaseModel):
    id: int
    username: str
    role: str
    approver_role: Optional[str] = None
    department: str
    display_name: str
    is_active: bool
    created_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
