# app/models/user.py
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship # Make sure this is imported
from app.db.base_class import Base

# from app.models.school_class import SchoolClass # If not already imported for other relationships

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    roll_number = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=True)
    hashed_password = Column(String, nullable=True)
    full_name = Column(String, index=True, nullable=True)
    is_active = Column(Boolean(), default=True)
    is_superuser = Column(Boolean(), default=False)
    role = Column(String, default="student", nullable=False)
    school_class_id = Column(
        Integer,
        ForeignKey("schoolclasses.id", name="fk_users_school_class_id_schoolclasses_id", ondelete="SET NULL"), # Ensure name matches Alembic
        nullable=True
    )
    enrolled_class = relationship(
        "SchoolClass",
        foreign_keys=[school_class_id],
        back_populates="students"
    )

    teaching_slots = relationship(
        "ClassScheduleSlot",
        back_populates="teacher")

    homeroom_classes_led = relationship(
        "SchoolClass",
        foreign_keys="SchoolClass.homeroom_teacher_id", # Corrected: string reference
        back_populates="homeroom_teacher",
        # primaryjoin="User.id == SchoolClass.homeroom_teacher_id" # Optional, usually inferred
    )

    # --- NEW RELATIONSHIPS FOR StudentAttendance ---
    # For Student's own attendance records
    attendance_records = relationship(
        "StudentAttendance", # Use string to avoid circular import
        foreign_keys="StudentAttendance.student_id", # String reference
        back_populates="student",
        cascade="all, delete-orphan" # If user is deleted, their attendance records are also deleted
    )

    # For records marked by this User (if they are a teacher)
    marked_student_attendance_records = relationship(
        "StudentAttendance",
        foreign_keys="StudentAttendance.marked_by_teacher_id", # String reference
        back_populates="marked_by_teacher"
        # No cascade here typically; deleting a teacher shouldn't delete records they marked,
        # the FK's ondelete="SET NULL" handles that.
    )

    # --- NEW RELATIONSHIPS FOR Task and Announcement ---
    created_tasks = relationship(
        "Task",
        foreign_keys="Task.created_by_teacher_id",
        back_populates="created_by_teacher"
    )

    created_announcements = relationship(
        "Announcement",
        foreign_keys="Announcement.created_by_user_id",
        back_populates="created_by_user"
    )
    # --- END NEW RELATIONSHIPS ---


    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"