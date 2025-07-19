# app/db/base.py
from app.db.base_class import Base
from app.models.auth.user import User
from app.models.academic.announcement import Announcement
from app.models.auth.recovery_code import RecoveryCode
from app.models.core.schedule import ClassScheduleSlot, Holiday
from app.models.core.school_class import SchoolClass
from app.models.attendance.student_attendance import StudentAttendance
from app.models.academic.task import Task, StudentTaskSubmission
from app.models.attendance.teacher_attendance import TeacherAttendance
from app.models.auth.webauthn import WebAuthnCredential, WebAuthnChallenge
