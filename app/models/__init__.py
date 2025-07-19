# Organized imports from subdirectories
from .auth import *
from .core import *
from .attendance import *
from .academic import *

# Re-export all models for backward compatibility
__all__ = [
    # Auth models
    "User", "RecoveryCode", "QRLoginSession", "WebAuthnCredential", "WebAuthnChallenge",
    # Core models
    "SchoolClass", "teacher_class_association", "ClassScheduleSlot", "Holiday",
    # Attendance models
    "StudentAttendance", "AttendanceSession", "AttendanceStatus", "TeacherAttendance",
    # Academic models
    "Task", "TaskStatus", "StudentTaskSubmission", "Announcement"
]