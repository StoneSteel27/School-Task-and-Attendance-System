from pydantic import BaseModel, ConfigDict
import datetime

class TeacherAttendanceBase(BaseModel):
    teacher_id: int

class TeacherAttendanceCreate(TeacherAttendanceBase):
    pass

class TeacherAttendanceUpdate(BaseModel):
    check_out_time: datetime.datetime
    status: str

class TeacherAttendanceInDB(TeacherAttendanceBase):
    id: int
    check_in_time: datetime.datetime
    check_out_time: datetime.datetime | None
    status: str

    model_config = ConfigDict(from_attributes=True)
