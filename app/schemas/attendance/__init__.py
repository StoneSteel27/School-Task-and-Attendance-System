# Attendance tracking schemas
from .student_attendance import *
from .teacher_attendance import *
from .attendance import *

__all__ = [
    # Student attendance schemas (actual classes that exist)
    "StudentInfo", "SchoolClassInfo", "TeacherInfo",
    "StudentAttendanceBase", "StudentAttendanceRecord",
    "StudentAttendanceEntryInput", "ClassAttendanceSubmission",
    "ClassAttendanceSubmissionResultItem", "ClassAttendanceSubmissionResponse",
    "ClassAttendancePercentageSummary",
    "AttendanceSession", "AttendanceStatus",
    # Teacher attendance schemas (actual classes that exist)
    "TeacherAttendanceBase", "TeacherAttendanceCreate", "TeacherAttendanceUpdate", "TeacherAttendanceInDB",
    # General attendance schemas (actual classes that exist)
    "AttendanceRequest"
]