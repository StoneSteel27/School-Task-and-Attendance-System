# Attendance tracking endpoints
from .attendance import router as attendance_router
from .student_attendance_admin import router as student_attendance_admin_router
from .homeroom_attendance_teacher import router as homeroom_attendance_teacher_router

__all__ = ["attendance_router", "student_attendance_admin_router", "homeroom_attendance_teacher_router"]