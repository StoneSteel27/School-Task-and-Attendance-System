from sqlalchemy.orm import Session
from app.models.teacher_attendance import TeacherAttendance
from app.schemas.teacher_attendance import TeacherAttendanceCreate, TeacherAttendanceUpdate
from app.crud.base import CRUDBase
from app.models import User
import datetime

class CRUDTeacherAttendance(CRUDBase[TeacherAttendance, TeacherAttendanceCreate, TeacherAttendanceUpdate]):
    def get_last_check_in(self, db: Session, *, teacher_id: int) -> TeacherAttendance | None:
        """
        Gets the most recent 'checked-in' record for a teacher.
        """
        return db.query(TeacherAttendance)
            .filter(TeacherAttendance.teacher_id == teacher_id, TeacherAttendance.status == "checked-in")\
            .order_by(TeacherAttendance.check_in_time.desc())\
            .first()

    def create_check_in(self, db: Session, *, teacher: User) -> TeacherAttendance:
        """
        Creates a new check-in record for a teacher.
        """
        db_obj = TeacherAttendance(teacher_id=teacher.id, status="checked-in")
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update_check_out(self, db: Session, *, db_obj: TeacherAttendance) -> TeacherAttendance:
        """
        Updates an existing attendance record with a check-out time.
        """
        db_obj.check_out_time = datetime.datetime.utcnow()
        db_obj.status = "checked-out"
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

teacher_attendance = CRUDTeacherAttendance(TeacherAttendance)
