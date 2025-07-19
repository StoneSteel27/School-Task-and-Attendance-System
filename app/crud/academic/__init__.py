# Academic content CRUD operations
from . import crud_task
from . import crud_student_task_submission
from . import crud_announcement

# For backward compatibility, also export without prefix
from .crud_task import *
from .crud_student_task_submission import *
from .crud_announcement import *

# Export functions grouped by module name for easier access
task = crud_task
student_task_submission = crud_student_task_submission
announcement = crud_announcement

__all__ = [
    "crud_task", "crud_student_task_submission", "crud_announcement",
    "task", "student_task_submission", "announcement"
]
