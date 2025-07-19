# Core school structure schemas
from .school_class import *
from .schedule import *
from .subject import *
from .teacher_assigment import *

__all__ = [
    # School class schemas - using actual classes that exist
    "SchoolClassBase", "SchoolClassCreate", "SchoolClassUpdate", "SchoolClass",
    "TeacherSubjectDetail", "ClassTeacherAssignmentsCreate", "ClassTeacherAssignmentsRemove",
    "BatchAssignmentResult", "TeacherTeachingDetail", "ClassTeachingStaffDetail",
    "BulkStudentRollNumbers", "StudentAssignmentStatus",
    # Schedule schemas - using actual classes that exist
    "ClassScheduleSlotBase", "ClassScheduleSlotCreateInput", "ClassScheduleSlotsBulkCreate",
    "ClassScheduleSlotUpdate", "ClassScheduleSlot", "HolidayBase", "HolidayCreate", 
    "HolidayUpdate", "Holiday", "HolidayBulkCreate",
    # Subject schemas - using actual classes that exist
    "Subject",
    # Teacher assignment schemas - using actual classes that exist
    "TeacherAssignmentBase", "TeacherAssignmentCreate", "TeacherAssignmentSubject"
]