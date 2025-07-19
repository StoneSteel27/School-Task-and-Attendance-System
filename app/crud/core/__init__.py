# Core school structure CRUD operations
from . import crud_school_class
from . import crud_schedule
from . import crud_subject
from . import crud_teacher_assignment

# For backward compatibility, also export without prefix
from .crud_school_class import *
from .crud_schedule import *
from .crud_subject import *
from .crud_teacher_assignment import *

# Export functions grouped by module name for easier access
school_class = crud_school_class
schedule = crud_schedule
subject = crud_subject
teacher_assignment = crud_teacher_assignment

__all__ = [
    "crud_school_class", "crud_schedule", "crud_subject", "crud_teacher_assignment",
    "school_class", "schedule", "subject", "teacher_assignment"
]
