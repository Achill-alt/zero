from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import date, datetime


class ContractCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(default="")
    contract_type: str = Field(...)
    amount: Optional[float] = None
    party_a: str = Field(default="")
    party_b: str = Field(default="")
    start_date: date
    end_date: date
    template_id: Optional[int] = None


class ContractUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=200)
    content: Optional[str] = None
    contract_type: Optional[str] = None
    amount: Optional[float] = None
    party_a: Optional[str] = None
    party_b: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class ContractResponse(BaseModel):
    id: int
    title: str
    content: str
    contract_type: str
    amount: Optional[float] = None
    party_a: str
    party_b: str
    start_date: str
    end_date: str
    status: str
    creator_id: int
    template_id: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ContractListResponse(BaseModel):
    items: list[ContractResponse]
    total: int
    page: int
    page_size: int


class ContractTemplateCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    title_template: str = Field(default="")
    content_template: str = Field(default="")
    contract_type: str


class ContractTemplateResponse(BaseModel):
    id: int
    name: str
    title_template: str
    content_template: str
    contract_type: str
    creator_id: int
    is_active: bool
    created_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
