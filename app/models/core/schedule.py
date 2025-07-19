from sqlalchemy import Column, Integer, String, Date, ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import relationship
from app.db.base_class import Base  # Your SQLAlchemy declarative base


class ClassScheduleSlot(Base):
    __tablename__ = "class_schedule_slots"

    id = Column(Integer, primary_key=True, index=True)

    school_class_id = Column(Integer, ForeignKey("schoolclasses.id", ondelete="CASCADE"), nullable=False)
    teacher_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    subject_name = Column(String(100), nullable=False)
    day_of_week = Column(Integer, nullable=False)  # 0=Monday, 1=Tuesday, ..., 6=Sunday
    period_number = Column(Integer, nullable=False)  # e.g., 1, 2, 3...

    school_class = relationship("SchoolClass", back_populates="schedule_slots")
    teacher = relationship("User", back_populates="teaching_slots")

    __table_args__ = (
        UniqueConstraint('school_class_id', 'day_of_week', 'period_number', name='uq_class_day_period'),
        UniqueConstraint('teacher_id', 'day_of_week', 'period_number', name='uq_teacher_day_period'),
    )

    def __repr__(self):
        return (f"<ClassScheduleSlot(id={self.id}, class_id={self.school_class_id}, "
                f"teacher_id={self.teacher_id}, day={self.day_of_week}, "
                f"period={self.period_number}, subject='{self.subject_name}')>")


class Holiday(Base):
    __tablename__ = "holidays"

    id = Column(Integer, primary_key=True, index=True)
    # REMOVE: date = Column(Date, nullable=False, unique=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    description = Column(String(255), nullable=False)
    grade_filter = Column(String(100), nullable=True, comment="NULL for all grades, or specific grade identifier(s)")

    __table_args__ = (
        CheckConstraint('start_date <= end_date', name='ck_holiday_date_order'),
    )

    def __repr__(self):
        return (f"<Holiday(id={self.id}, description='{self.description}', "
                f"start='{self.start_date}', end='{self.end_date}', grade_filter='{self.grade_filter}')>")
