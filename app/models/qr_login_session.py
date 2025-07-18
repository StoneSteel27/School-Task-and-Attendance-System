from sqlalchemy import Column, String, DateTime, func, ForeignKey, Integer
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class QRLoginSession(Base):
    __tablename__ = "qr_login_sessions"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String, unique=True, index=True, nullable=False)
    status = Column(String, default="pending", nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    user = relationship("User")
