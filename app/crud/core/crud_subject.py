from sqlalchemy.orm import Session
from app.models.core.school_class import teacher_class_association
from app.models.auth.user import User
from app.schemas.core.subject import Subject


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


# Create a simple object to provide access to all subject CRUD functions
class CRUDSubject:
    """CRUD operations for Subject model"""

    def get_subjects_by_class(self, db: Session, *, class_id: int):
        return get_subjects_by_class(db, class_id=class_id)


# Create the instance that will be imported
subject = CRUDSubject()
