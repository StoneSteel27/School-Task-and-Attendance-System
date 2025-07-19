# app/models/student_attendance.py
import enum
from sqlalchemy import Column, Integer, Date, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base
from sqlalchemy import Enum as SAEnum # Generic Enum for SQLAlchemy

# Define Enums for status and session
# Inheriting from str and enum.Enum makes them compatible with Pydantic and FastAPI
class AttendanceSession(str, enum.Enum):
    MORNING = "MORNING"
    AFTERNOON = "AFTERNOON"

class AttendanceStatus(str, enum.Enum):
    PRESENT = "PRESENT"
    ABSENT = "ABSENT"

class StudentAttendance(Base):
    __tablename__ = "student_attendance"

    id = Column(Integer, primary_key=True, index=True)

    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    school_class_id = Column(Integer, ForeignKey("schoolclasses.id", ondelete="CASCADE"), nullable=False, index=True)
    marked_by_teacher_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    attendance_date = Column(Date, nullable=False, index=True)
    # Using native_enum=False for SQLite compatibility if it struggles with native ENUM types
    # For PostgreSQL/MySQL, native_enum=True is generally better.
    # Let's keep create_constraint=True which is good practice for databases that support it.
    # values_callable is good for Alembic autogenerate if native_enum=True might be an issue.
    session = Column(
        SAEnum(AttendanceSession, name="attendance_session_enum", create_constraint=True, native_enum=False, values_callable=lambda x: [e.value for e in x]),
        nullable=False
    )
    status = Column(
        SAEnum(AttendanceStatus, name="attendance_status_enum", create_constraint=True, native_enum=False, values_callable=lambda x: [e.value for e in x]),
        nullable=False
    )

    created_at = Column(DateTime, default=func.now(), nullable=False)

    # Relationships
    student = relationship("User", foreign_keys=[student_id], back_populates="attendance_records")
    school_class = relationship("SchoolClass", foreign_keys=[school_class_id], back_populates="student_attendance_records")
    marked_by_teacher = relationship("User", foreign_keys=[marked_by_teacher_id], back_populates="marked_student_attendance_records")

    __table_args__ = (
        UniqueConstraint('student_id', 'attendance_date', 'session', name='uq_student_attendance_date_session'),
        # The naming convention in base_class.py will derive the actual PK/FK/IX/UQ constraint names
        # like pk_student_attendance, fk_student_attendance_student_id_users_id etc.
        # The name provided in UniqueConstraint here is an internal SQLAlchemy name for the constraint object,
        # which Alembic might use in generated migration.
    )

    def __repr__(self):
        return f"<StudentAttendance(id={self.id}, student_id={self.student_id}, date={self.attendance_date}, session='{self.session.value if self.session else None}', status='{self.status.value if self.status else None}')>"