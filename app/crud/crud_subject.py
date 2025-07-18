from sqlalchemy.orm import Session
from app.models.school_class import teacher_class_association
from app.models.user import User
from app.schemas.subject import Subject


def get_subjects_by_class(db: Session, *, class_id: int) -> list[Subject]:
    results = (
        db.query(
            teacher_class_association.c.subject,
            User.full_name
        )
        .join(User, teacher_class_association.c.teacher_id == User.id)
        .filter(teacher_class_association.c.class_id == class_id)
        .all()
    )
    subjects = [Subject(name=subject, teacher_name=teacher_name) for subject, teacher_name in results]
    return subjects
