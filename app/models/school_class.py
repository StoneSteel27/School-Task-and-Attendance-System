from sqlalchemy import Column, Integer, String, ForeignKey, Table, PrimaryKeyConstraint
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class SchoolClass(Base):
    __tablename__ = "schoolclasses"

    id = Column(Integer, primary_key=True, index=True)
    class_code = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String, index=True, nullable=False)
    grade = Column(String, nullable=True)
    section = Column(String, nullable=True)
    description = Column(String, nullable=True)

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
        "User",  # The User model
        secondary=lambda: teacher_class_association,
        backref="teaching_classes_association")

    def __repr__(self):
        return f"<SchoolClass(id={self.id}, class_code='{self.class_code}', name='{self.name}')>"


teacher_class_association = Table(
    'teacher_class_association', Base.metadata,
    Column('teacher_id', Integer, ForeignKey('users.id', ondelete="CASCADE")),
    Column('class_id', Integer, ForeignKey('schoolclasses.id', ondelete="CASCADE")),
    Column('subject', String(100), nullable=False),
    PrimaryKeyConstraint('teacher_id', 'class_id', 'subject', name='pk_teacher_class_subject_association')
)
