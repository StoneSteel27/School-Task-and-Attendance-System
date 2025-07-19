# Organized imports from subdirectories
from .auth import *
from .core import *
from .attendance import *
from .academic import *

# Re-export all schemas for backward compatibility
__all__ = [
    # Auth schemas
    "UserBase", "UserCreate", "UserUpdate", "User", "UserInDB",
    "RecoveryCodeCreate", "RecoveryCode",
    "QRLoginSessionCreate", "QRLoginSession", "QRLoginRequest", "QRLoginResponse",
    "Token", "TokenPayload",
    "WebAuthnCredentialCreate", "WebAuthnCredential", "WebAuthnChallengeCreate", "WebAuthnChallenge",
    # Core schemas
    "SchoolClassBase", "SchoolClassCreate", "SchoolClassUpdate", "SchoolClass", "SchoolClassInDB",
    "ClassScheduleSlotBase", "ClassScheduleSlotCreate", "ClassScheduleSlotUpdate", "ClassScheduleSlot",
    "HolidayBase", "HolidayCreate", "HolidayUpdate", "Holiday",
    "SubjectCreate", "Subject",
    "TeacherAssignmentCreate", "TeacherAssignment",
    # Attendance schemas
    "StudentAttendanceBase", "StudentAttendanceCreate", "StudentAttendanceUpdate", "StudentAttendance",
    "AttendanceSession", "AttendanceStatus",
    "TeacherAttendanceBase", "TeacherAttendanceCreate", "TeacherAttendanceUpdate", "TeacherAttendance",
    "AttendanceResponse", "AttendanceRequest",
    # Academic schemas
    "TaskBase", "TaskCreate", "TaskUpdate", "Task", "TaskStatus",
    "StudentTaskSubmissionBase", "StudentTaskSubmissionCreate", "StudentTaskSubmissionUpdate", "StudentTaskSubmission",
    "AnnouncementBase", "AnnouncementCreate", "AnnouncementUpdate", "Announcement"
]
