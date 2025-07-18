# app/db/base.py
from app.db.base_class import Base
from app.models.user import User
from app.models.announcement import Announcement
from app.models.recovery_code import RecoveryCode
from app.models.schedule import ClassScheduleSlot, Holiday
from app.models.school_class import SchoolClass
from app.models.student_attendance import StudentAttendance
from app.models.task import Task, StudentTaskSubmission
from app.models.teacher_attendance import TeacherAttendance
from app.models.webauthn import WebAuthnCredential, WebAuthnChallenge
