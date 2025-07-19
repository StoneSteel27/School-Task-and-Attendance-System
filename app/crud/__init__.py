# Organized imports from subdirectories
from .auth import *
from .core import *
from .attendance import *
from .academic import *

# Re-export all CRUD operations for backward compatibility and direct access
__all__ = [
    # Auth CRUD - with crud_ prefix
    "crud_user", "crud_recovery_code", "crud_qr_login_session", "crud_webauthn",
    # Auth CRUD - without prefix (backward compatibility)
    "user", "recovery_code", "qr_login_session", "webauthn",
    # Core CRUD - with crud_ prefix
    "crud_school_class", "crud_schedule", "crud_subject", "crud_teacher_assignment",
    # Core CRUD - without prefix (backward compatibility)
    "school_class", "schedule", "subject", "teacher_assignment",
    # Attendance CRUD - with crud_ prefix
    "crud_student_attendance", "crud_teacher_attendance",
    # Attendance CRUD - without prefix (backward compatibility)
    "student_attendance", "teacher_attendance",
    # Academic CRUD - with crud_ prefix
    "crud_task", "crud_student_task_submission", "crud_announcement",
    # Academic CRUD - without prefix (backward compatibility)
    "task", "student_task_submission", "announcement"
]