from pydantic import BaseModel, Field, ConfigDict
from typing import List

class TeacherAssignmentBase(BaseModel):
    subject: str = Field(..., min_length=1, description="The subject the teacher is assigned to teach in the class.")

class TeacherAssignmentCreate(TeacherAssignmentBase):
    # This schema will be used as the request body when assigning a teacher to a subject in a class.
    # The teacher_roll_number and class_code will come from the URL path.
    pass

class TeacherAssignmentSubject(BaseModel): # Represents a subject a teacher teaches in a class
    subject: str

    model_config = ConfigDict(from_attributes=True)
