# Academic content schemas
from .task import *
from .announcement import *

__all__ = [
    # Task schemas
    "TaskBase", "TaskCreate", "TaskUpdate", "Task", "TaskStatus",
    "StudentTaskSubmissionBase", "StudentTaskSubmissionCreate", "StudentTaskSubmissionUpdate", "StudentTaskSubmission",
    # Announcement schemas
    "AnnouncementBase", "AnnouncementCreate", "AnnouncementUpdate", "Announcement"
]