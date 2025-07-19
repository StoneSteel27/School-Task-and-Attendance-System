# Attendance tracking CRUD operations
from . import crud_student_attendance
from . import crud_teacher_attendance

# For backward compatibility, also export without prefix
from .crud_student_attendance import *
from .crud_teacher_attendance import *

# Export functions grouped by module name for easier access
student_attendance = crud_student_attendance
teacher_attendance = crud_teacher_attendance

__all__ = [
    "crud_student_attendance", "crud_teacher_attendance",
    "student_attendance", "teacher_attendance"
]
