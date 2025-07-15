# app/models/school_class.py
from sqlalchemy import Column, Integer, String, ForeignKey, Table, PrimaryKeyConstraint
from sqlalchemy.orm import relationship # Make sure this is imported

from app.db.base_class import Base

class SchoolClass(Base):
    __tablename__ = "schoolclasses"

    id = Column(Integer, primary_key=True, index=True)
    class_code = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String, index=True, nullable=False)
    grade = Column(String, nullable=True)
    section = Column(String, nullable=True)
    description = Column(String, nullable=True)

    homeroom_teacher_id = Column(
        Integer,
        ForeignKey("users.id", name="fk_schoolclasses_homeroom_teacher_id_users_id", ondelete="SET NULL"),
        nullable=True
    )

    schedule_slots = relationship(
        "ClassScheduleSlot",
        back_populates="school_class",
        cascade="all, delete-orphan")

    students = relationship(
        "User",
        primaryjoin="User.school_class_id == SchoolClass.id",
        back_populates="enrolled_class"
    )

    teachers_association = relationship(
        "User",
        secondary="teacher_class_association", # String reference
        backref="teaching_classes_association" # backref is fine for simple cases
    )

    homeroom_teacher = relationship(
        "User",
        back_populates="homeroom_classes_led",
        foreign_keys=[homeroom_teacher_id]
    )

    student_attendance_records = relationship(
        "StudentAttendance", # Use string to avoid circular import
        foreign_keys="StudentAttendance.school_class_id", # String reference
        back_populates="school_class",
        cascade="all, delete-orphan" # If class is deleted, its attendance records are also deleted
    )

    # --- NEW RELATIONSHIPS FOR Task and Announcement ---
    tasks = relationship(
        "Task",
        back_populates="school_class",
        cascade="all, delete-orphan"
    )

    announcements = relationship(
        "Announcement",
        back_populates="school_class",
        cascade="all, delete-orphan"
    )
    # --- END NEW RELATIONSHIPS ---

    def __repr__(self):
        return f"<SchoolClass(id={self.id}, class_code='{self.class_code}', name='{self.name}')>"

teacher_class_association = Table(
    'teacher_class_association', Base.metadata,
    Column('teacher_id', Integer, ForeignKey('users.id', ondelete="CASCADE")),
    Column('class_id', Integer, ForeignKey('schoolclasses.id', ondelete="CASCADE")),
    Column('subject', String(100), nullable=False),
    PrimaryKeyConstraint('teacher_id', 'class_id', 'subject', name='pk_teacher_class_subject_association')
)