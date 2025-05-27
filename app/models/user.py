from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base_class import Base


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
    school_class_id = Column(Integer, ForeignKey("schoolclasses.id", name="fk_user_school_class", ondelete="SET NULL"), nullable=True)
    enrolled_class = relationship(
        "SchoolClass",  # Target model as a string
        foreign_keys=[school_class_id],  # Explicitly state the FK
        back_populates="students"  # Matches `students` relationship in SchoolClass
    )

    teaching_slots = relationship(
        "ClassScheduleSlot",
        back_populates="teacher")

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}, role='{self.role}')>"
