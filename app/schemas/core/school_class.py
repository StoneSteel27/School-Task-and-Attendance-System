from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional

from app.schemas.auth.user import User as UserSchema


class SchoolClassBase(BaseModel):
    class_code: str = Field(..., description="Unique code for the class, e.g., GR10-A-2024")
    name: str = Field(..., description="Descriptive name of the class, e.g., Grade 10 Section A")
    grade: Optional[str] = None
    section: Optional[str] = None
    description: Optional[str] = None


class SchoolClassCreate(SchoolClassBase):
    pass


class SchoolClassUpdate(BaseModel):  # Doesn't inherit Base to make all fields truly optional
    class_code: Optional[str] = None
    name: Optional[str] = None
    grade: Optional[str] = None
    section: Optional[str] = None
    description: Optional[str] = None
    homeroom_teacher_id: Optional[int] = Field(None,
                                               description="ID of the user to be assigned as homeroom teacher.")  # <<<< NEWLY ADDED




class TeacherSubjectDetail(BaseModel): # Input for batch operations
    teacher_roll_number: str
    subject: str = Field(..., description="The subject the teacher will teach.")

class ClassTeacherAssignmentsCreate(BaseModel): # Payload for batch assignment POST
    assignments: List[TeacherSubjectDetail] = Field(..., min_length=1)

class ClassTeacherAssignmentsRemove(BaseModel): # Payload for batch removal POST
    assignments: List[TeacherSubjectDetail] = Field(..., min_length=1) # Same structure for identifying what to remove

class BatchAssignmentResult(BaseModel): # For the response of batch operations
    teacher_roll_number: str
    subject: str
    status: str # e.g., "assigned", "removed", "already_exists", "not_found", "error_teacher_not_found",
    # "error_not_a_teacher", "error_unknown"
    detail: Optional[str] = None


class TeacherTeachingDetail(BaseModel):
    school_class_code: str
    school_class_name: str
    subject: str


class ClassTeachingStaffDetail(BaseModel):
    teacher_roll_number: str
    teacher_full_name: Optional[str] = None
    subject: str

class SchoolClass(SchoolClassBase):  # Inherits from SchoolClassBase
    id: int
    students: List[UserSchema] = []
    teaching_staff: List[ClassTeachingStaffDetail] = []
    homeroom_teacher_id: Optional[int] = Field(None, description="ID of the assigned homeroom teacher.")

    model_config = ConfigDict(from_attributes=True)  # Use model_config


class BulkStudentRollNumbers(BaseModel):
    student_roll_numbers: List[str] = Field(..., min_length=1, description="A list of student roll numbers to assign or unassign from the class.")

class StudentAssignmentStatus(BaseModel):
    student_roll_number: str
    status: str  # e.g., "assigned", "unassigned", "error_student_not_found", "error_not_a_student", "error_already_in_this_class", "error_already_in_another_class", "error_not_in_this_class_for_unassign"
    detail: Optional[str] = None
    conflicting_class_code: Optional[str] = None # To indicate which class the student is already in, if applicable during assignment

    model_config = ConfigDict(from_attributes=True)  # Use model_config