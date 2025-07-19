# Organized imports from subdirectories
from .auth import *
from .core import *
from .attendance import *
from .academic import *

# Re-export all endpoint routers for backward compatibility
__all__ = [
    # Auth endpoints
    "auth_router", "qr_login_router", "recovery_router", "users_router", "users_admin_router",
    # Core endpoints
    "classes_router", "holidays_router", "students_router", "teachers_router", 
    "classes_admin_router", "holidays_admin_router", "students_teacher_router",
    # Attendance endpoints
    "attendance_router", "student_attendance_admin_router", "homeroom_attendance_teacher_router",
    # Academic endpoints
    "announcements_admin_router", "submissions_teacher_router", "tasks_announcements_teacher_router"
]