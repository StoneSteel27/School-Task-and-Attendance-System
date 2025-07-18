import datetime
from sqlalchemy import Column, Integer, ForeignKey, DateTime, String
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class TeacherAttendance(Base):
    __tablename__ = "teacher_attendance"

    id = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    check_in_time = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    check_out_time = Column(DateTime, nullable=True)
    status = Column(String, default="checked-in", nullable=False) # e.g., "checked-in", "checked-out"

    teacher = relationship("User", back_populates="teacher_attendance_records")

# Add the corresponding relationship to the User model
from app.models.user import User
User.teacher_attendance_records = relationship("TeacherAttendance", back_populates="teacher", cascade="all, delete-orphan")
