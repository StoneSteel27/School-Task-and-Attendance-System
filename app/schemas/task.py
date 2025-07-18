from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict

from app.models.task import TaskStatus # Import the Enum from the model

# --- Base Schemas ---
class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Title of the task.")
    description: Optional[str] = Field(None, description="Detailed description of the task.")
    due_date: date = Field(..., description="The date by which the task is due.")
    attachment_url: Optional[str] = Field(None, description="URL to an optional attachment for the task.")
    subject: str = Field(..., min_length=1, max_length=100, description="The subject this task belongs to (e.g., 'Mathematics', 'History').")


# --- Create Schemas ---
class TaskCreate(TaskBase):
    # When creating, school_class_id and created_by_teacher_id will be derived from context (path/auth)
    pass


# --- Update Schemas ---
class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255, description="New title of the task.")
    description: Optional[str] = Field(None, description="New detailed description of the task.")
    due_date: Optional[date] = Field(None, description="New due date for the task.")
    attachment_url: Optional[str] = Field(None, description="New URL to an optional attachment for the task.")
    subject: Optional[str] = Field(None, min_length=1, max_length=100, description="New subject this task belongs to.")


# --- Full Task Schema (for responses) ---
class Task(TaskBase):
    id: int = Field(..., description="Unique ID of the task.")
    created_by_teacher_id: Optional[int] = Field(None, description="ID of the teacher who created the task.")
    school_class_id: int = Field(..., description="ID of the school class this task is for.")
    created_at: datetime = Field(..., description="Timestamp when the task was created.")
    updated_at: datetime = Field(..., description="Timestamp when the task was last updated.")

    # Nested relationships (optional, depending on how much detail is needed in response)
    # from .user import User as UserSchema # Assuming UserSchema is defined
    # created_by_teacher: Optional[UserSchema] = None
    # from .school_class import SchoolClassBase as SchoolClassSchema # Assuming SchoolClassSchema is defined
    # school_class: Optional[SchoolClassSchema] = None

    model_config = ConfigDict(from_attributes=True)


# --- Student Task Submission Schemas ---
# This is a conceptual schema for student submission, not directly tied to the Task model above.
# It would be a separate model/schema for tracking each student's submission for a given task.
class StudentTaskSubmissionBase(BaseModel):
    task_id: int = Field(..., description="ID of the task being submitted.")
    student_id: int = Field(..., description="ID of the student submitting the task.")
    submission_url: Optional[str] = Field(None, description="URL to the submitted file/resource.")
    status: TaskStatus = Field(TaskStatus.PENDING, description="Current status of the submission.")

class StudentTaskSubmissionCreate(StudentTaskSubmissionBase):
    pass

class StudentTaskSubmissionUpdate(BaseModel):
    submission_url: Optional[str] = Field(None, description="New URL to the submitted file/resource.")
    status: Optional[TaskStatus] = Field(None, description="New status of the submission.")

class StudentTaskSubmission(StudentTaskSubmissionBase):
    id: int
    submitted_at: datetime = Field(..., description="Timestamp when the task was submitted.")
    approved_at: Optional[datetime] = Field(None, description="Timestamp when the task was approved.")

    model_config = ConfigDict(from_attributes=True)


class TaskWithSubmissionStatus(Task):
    submission_status: Optional[TaskStatus] = Field(None, description="The current submission status for the student.")
    submission_url: Optional[str] = Field(None, description="The URL of the student's submission.")
    submitted_at: Optional[datetime] = Field(None, description="The timestamp of the student's submission.")
