from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Any


class ApprovalChainCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    conditions: dict[str, Any] = Field(default_factory=dict)
    steps: list[dict[str, Any]] = Field(default_factory=list)
    priority: int = Field(default=0)
    is_active: bool = True


class ApprovalChainUpdate(BaseModel):
    name: Optional[str] = None
    conditions: Optional[dict[str, Any]] = None
    steps: Optional[list[dict[str, Any]]] = None
    priority: Optional[int] = None
    is_active: Optional[bool] = None


class ApprovalChainResponse(BaseModel):
    id: int
    name: str
    conditions: Any
    steps: Any
    priority: int
    is_active: bool
    created_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ApprovalAction(BaseModel):
    comment: str = Field(default="")


class ApprovalInstanceResponse(BaseModel):
    id: int
    contract_id: int
    template_id: int
    current_step_index: int
    status: str
    step_results: Any
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
