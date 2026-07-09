from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from sqlalchemy.sql import func
from app.database import Base


class ApprovalChainTemplate(Base):
    __tablename__ = "approval_chain_templates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    conditions = Column(Text, nullable=False, default="{}")  # JSON
    steps = Column(Text, nullable=False, default="[]")  # JSON array
    priority = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())


class ApprovalInstance(Base):
    __tablename__ = "approval_instances"

    id = Column(Integer, primary_key=True, autoincrement=True)
    contract_id = Column(Integer, nullable=False, index=True)
    template_id = Column(Integer, nullable=False)
    current_step_index = Column(Integer, default=0)
    status = Column(String(20), nullable=False, default="in_progress")  # in_progress, approved, rejected, withdrawn
    step_results = Column(Text, default="[]")  # JSON array
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
