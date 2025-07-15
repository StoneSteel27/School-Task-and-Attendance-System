from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base

class Announcement(Base):
    __tablename__ = "announcements"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    content = Column(String, nullable=False)
    attachment_url = Column(String, nullable=True) # URL to a file storage

    # Foreign Keys
    created_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True) # Can be teacher or principal
    school_class_id = Column(Integer, ForeignKey("schoolclasses.id", ondelete="CASCADE"), nullable=True) # Null for school-wide
    subject = Column(String(100), nullable=True) # Null for school-wide or class-wide, specific for subject-level

    is_school_wide = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime, default=func.now(), nullable=False)

    # Relationships
    created_by_user = relationship("User", foreign_keys=[created_by_user_id], back_populates="created_announcements")
    school_class = relationship("SchoolClass", back_populates="announcements")

    def __repr__(self):
        return f"<Announcement(id={self.id}, title='{self.title}', is_school_wide={self.is_school_wide})>"
