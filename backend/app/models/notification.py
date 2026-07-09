from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database import Base


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    type = Column(String(32), nullable=False)       # approval_new | approval_result
    title = Column(String(255), nullable=False)
    content = Column(String(500), nullable=True)
    is_read = Column(Boolean, default=False)
    related_id = Column(Integer, nullable=True)      # related contract ID
    created_at = Column(DateTime, server_default=func.now())
