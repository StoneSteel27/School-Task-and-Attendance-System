from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base
import enum

class TaskStatus(str, enum.Enum):
    PENDING = "PENDING"
    SUBMITTED = "SUBMITTED"
    APPROVED = "APPROVED"

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(String, nullable=True)
    due_date = Column(Date, nullable=False)
    attachment_url = Column(String, nullable=True) # URL to a file storage

    # Foreign Keys
    created_by_teacher_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    school_class_id = Column(Integer, ForeignKey("schoolclasses.id", ondelete="CASCADE"), nullable=False)
    subject = Column(String(100), nullable=False) # Subject within the class

    # Status for student submission (each student will have their own status for a task)
    # This model represents the task itself, not individual student submissions.
    # Student submission status will be handled by a separate model (e.g., TaskSubmission)
    # For now, we'll assume the task itself doesn't have a global status, but individual student submissions do.

    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    created_by_teacher = relationship("User", foreign_keys=[created_by_teacher_id], back_populates="created_tasks")
    school_class = relationship("SchoolClass", back_populates="tasks")

    def __repr__(self):
        return f"<Task(id={self.id}, title='{self.title}', class_id={self.school_class_id}, subject='{self.subject}')>"
