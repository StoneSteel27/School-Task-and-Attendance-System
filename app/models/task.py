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


class StudentTaskSubmission(Base):
    __tablename__ = "student_task_submissions"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    submission_url = Column(String, nullable=True) # URL or path to the submitted file/resource
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING, nullable=False)

    submitted_at = Column(DateTime, default=func.now(), nullable=False)
    approved_at = Column(DateTime, nullable=True)

    # Relationships
    task = relationship("Task", backref="submissions")
    student = relationship("User", backref="task_submissions")

    def __repr__(self):
        return f"<StudentTaskSubmission(id={self.id}, task_id={self.task_id}, student_id={self.student_id}, status='{self.status}')>"
