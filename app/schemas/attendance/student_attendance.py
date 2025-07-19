# app/schemas/student_attendance.py
from datetime import date, datetime
from typing import List, Optional, Dict
from pydantic import BaseModel, Field, ConfigDict

# Import the enums from the models file as they are the source of truth for these values
from app.models.attendance.student_attendance import AttendanceSession, AttendanceStatus

# For richer responses, we'll define minimal schemas or import existing ones
# We'll use existing User and SchoolClass schemas if they are suitable,
# otherwise, we'd create specific minimal versions here.
# For now, let's assume we might want basic info from User and SchoolClass.
from app.schemas.auth.user import User as UserSchema  # For student and teacher info
from app.schemas.core.school_class import SchoolClassBase as SchoolClassInfoSchema  # For basic class info


# --- Minimal Schemas for Embedding in Responses (if needed) ---
# These help control the amount of data sent back and avoid circular dependencies
# if the main UserSchema or SchoolClassSchema are too verbose or have deep nesting.

class StudentInfo(BaseModel):  # For StudentAttendanceRecord
    id: int
    roll_number: str
    full_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)  # Use model_config


class SchoolClassInfo(BaseModel):  # For StudentAttendanceRecord
    id: int
    class_code: str
    name: str  # Or just class_code if name is not crucial here

    model_config = ConfigDict(from_attributes=True)  # Use model_config


class TeacherInfo(BaseModel):  # For StudentAttendanceRecord
    id: int
    full_name: Optional[str] = None

    # roll_number: Optional[str] = None # if needed

    model_config = ConfigDict(from_attributes=True)  # Use model_config


# --- Core Attendance Record Schema (for DB interaction and GET responses) ---
class StudentAttendanceBase(BaseModel):  # More for internal use or as a base for ORM model
    student_id: int
    school_class_id: int
    marked_by_teacher_id: int
    attendance_date: date
    session: AttendanceSession
    status: AttendanceStatus


class StudentAttendanceRecord(BaseModel):  # For API GET responses if we fetch individual records
    id: int
    attendance_date: date
    session: AttendanceSession
    status: AttendanceStatus
    created_at: datetime

    # Embed related information
    student: StudentInfo
    school_class: SchoolClassInfo
    marked_by_teacher: TeacherInfo

    model_config = ConfigDict(from_attributes=True)  # Use model_config


# --- Schema for Teacher's Single Submission for their Whole Class ---
class StudentAttendanceEntryInput(BaseModel):
    student_id: int = Field(..., description="The database ID of the student.")
    status: AttendanceStatus = Field(..., description="Attendance status for the student (PRESENT or ABSENT).")


class ClassAttendanceSubmission(BaseModel):  # Request body for teacher's submission
    attendance_date: date = Field(..., description="The date for which attendance is being recorded.")
    session: AttendanceSession = Field(..., description="The session (MORNING or AFTERNOON).")
    # school_class_id will be determined by the endpoint (e.g., homeroom teacher's class)
    # marked_by_teacher_id will be determined by the endpoint (authenticated user)
    entries: List[StudentAttendanceEntryInput] = Field(...,
                                                       description="List of attendance entries for students in the class.",
                                                       min_length=0)
    # min_length=0 allows submitting an empty list if the class has no students, though the UI should prevent this.
    # Or min_length=1 if a class must have students.


# --- Response Schema for the Class Attendance Submission ---
class ClassAttendanceSubmissionResultItem(BaseModel):
    student_id: int
    # For better UX, include some student identifiers from the User model
    student_roll_number: str  # Made non-optional, assuming student exists if processed
    student_full_name: Optional[str] = None

    submitted_status: AttendanceStatus  # The status submitted by the teacher
    outcome: str = Field(...,
                         description="Outcome: SUCCESS, ERROR_STUDENT_NOT_FOUND_IN_SYSTEM, ERROR_STUDENT_NOT_IN_SPECIFIED_CLASS, ERROR_ALREADY_RECORDED, ERROR_INVALID_STATUS, ERROR_UNKNOWN")
    message: Optional[str] = None
    record_id: Optional[int] = Field(None, description="ID of the created StudentAttendance record if successful.")


class ClassAttendanceSubmissionResponse(BaseModel):
    school_class_id: int
    school_class_code: str  # For context in response
    attendance_date: date
    session: AttendanceSession
    marked_by_teacher_id: int
    marked_by_teacher_name: Optional[str] = None  # For context

    total_students_in_payload: int
    successful_records: int
    failed_records: int

    results: List[ClassAttendanceSubmissionResultItem]


class ClassAttendancePercentageSummary(BaseModel):
    """
    Provides a summary of attendance percentages and counts for a class
    on a specific date and session.
    """
    school_class_id: int = Field(..., description="The database ID of the school class.")
    school_class_code: str = Field(..., description="The unique code of the school class.")
    school_class_name: str = Field(..., description="The descriptive name of the school class.")
    attendance_date: date = Field(..., description="The date for which the attendance summary is generated.")
    session: AttendanceSession = Field(..., description="The attendance session (MORNING or AFTERNOON).")

    total_students_enrolled: int = Field(..., description="Total number of students officially enrolled in the class.")
    total_marked: int = Field(...,
                              description="Total number of enrolled students for whom attendance (PRESENT or ABSENT) was recorded for this session.")
    total_present: int = Field(..., description="Number of enrolled students marked as PRESENT for this session.")
    total_absent: int = Field(..., description="Number of enrolled students marked as ABSENT for this session.")
    total_unmarked: int = Field(...,
                                description="Number of enrolled students for whom no attendance record (PRESENT or ABSENT) exists for this session.")

    attendance_percentage: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Percentage of *marked* students who were PRESENT. (total_present / total_marked) * 100. Returns 0.0 if no students were marked."
    )
    marking_completeness_percentage: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Percentage of *enrolled* students who have an attendance mark (PRESENT or ABSENT) for this session. (total_marked / total_students_enrolled) * 100. Returns 0.0 if no students are enrolled."
    )

    model_config = ConfigDict(from_attributes=True)  # Use model_config
