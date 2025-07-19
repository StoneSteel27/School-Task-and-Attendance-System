from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.auth.user import User
from app.models.core.school_class import SchoolClass, teacher_class_association


def assign_teacher_to_class_subject(
        db: Session,
        *,
        teacher: User,
        school_class: SchoolClass,
        subject: str
) -> bool:  # Returns True if assignment was created, could also return the association object or raise specific errors
    """
    Assigns a teacher to teach a specific subject in a school class.
    Populates the teacher_class_association table.
    """
    if teacher.role != "teacher":
        raise ValueError(f"User {teacher.roll_number} is not a teacher and cannot be assigned to teach.")

    # Create an insert statement for the association table
    stmt = teacher_class_association.insert().values(
        teacher_id=teacher.id,
        class_id=school_class.id,
        subject=subject
    )
    try:
        db.execute(stmt)
        db.commit()
        return True
    except IntegrityError:  # Handles cases where the (teacher_id, class_id, subject) PK already exists
        db.rollback()
        # Optionally, log this or return a specific status/error
        # For now, let's consider it not an error if it already exists, or let API handle 409 Conflict
        # Re-raising for now, API can decide how to handle (e.g. 409 Conflict if already exists)
        raise
    except Exception:
        db.rollback()
        raise


def unassign_teacher_from_class_subject(
        db: Session,
        *,
        teacher: User,
        school_class: SchoolClass,
        subject: str
) -> bool:  # Returns True if an assignment was deleted
    """
    Unassigns a teacher from teaching a specific subject in a school class.
    """
    # Create a delete statement for the association table
    stmt = teacher_class_association.delete().where(
        teacher_class_association.c.teacher_id == teacher.id,
        teacher_class_association.c.class_id == school_class.id,
        teacher_class_association.c.subject == subject
    )
    result = db.execute(stmt)
    db.commit()
    return result.rowcount > 0  # Returns True if one or more rows were deleted


def get_assignments_for_teacher(
        db: Session, *, teacher: User
) -> list[dict]:
    """
    Retrieves all class/subject assignments for a given teacher.
    """
    query_result = db.query(
        SchoolClass.id,
        SchoolClass.class_code,
        SchoolClass.name,
        teacher_class_association.c.subject
    ).join(
        teacher_class_association,
        SchoolClass.id == teacher_class_association.c.class_id
    ).filter(
        teacher_class_association.c.teacher_id == teacher.id
    ).order_by(SchoolClass.class_code, teacher_class_association.c.subject).all()

    return [
        {
            "school_class_id": row.id,
            "school_class_code": row.class_code,
            "school_class_name": row.name,
            "subject": row.subject
        }
        for row in query_result
    ]


def get_teachers_for_class_subject(  # Might not be needed if we have get_teachers_for_class
        db: Session, *, school_class: SchoolClass, subject: str
) -> list[User]:
    """
    Retrieves all teachers assigned to a specific subject in a specific class.
    (Usually, this might be one teacher per subject per class, but the model allows many)
    """
    return db.query(User).join(
        teacher_class_association,
        User.id == teacher_class_association.c.teacher_id
    ).filter(
        teacher_class_association.c.class_id == school_class.id,
        teacher_class_association.c.subject == subject
    ).all()


def get_teaching_staff_for_class(
        db: Session, *, school_class: SchoolClass
) -> list[dict]:  # Returns list of dicts like {"teacher_roll_number": "X", "teacher_full_name": "Y", "subject": "Z"}
    """
    Retrieves all teachers and their subjects for a given class.
    """
    query_result = db.query(
        User.roll_number,
        User.full_name,
        teacher_class_association.c.subject
    ).join(
        teacher_class_association,
        User.id == teacher_class_association.c.teacher_id
    ).filter(
        teacher_class_association.c.class_id == school_class.id
    ).order_by(User.roll_number, teacher_class_association.c.subject).all()

    return [
        {"teacher_roll_number": row.roll_number, "teacher_full_name": row.full_name, "subject": row.subject}
        for row in query_result
    ]


def check_teacher_assigned_to_class_subject(
        db: Session, *, teacher: User, school_class: SchoolClass, subject: str
) -> bool:
    """
    Checks if a specific teacher is assigned to teach a specific subject in a specific class.
    """
    return db.query(teacher_class_association).filter(
        teacher_class_association.c.teacher_id == teacher.id,
        teacher_class_association.c.class_id == school_class.id,
        teacher_class_association.c.subject == subject
    ).first() is not None


# Create a simple object to provide access to all teacher assignment CRUD functions
class CRUDTeacherAssignment:
    """CRUD operations for Teacher Assignment model"""
    
    def assign_teacher_to_class_subject(self, db: Session, *, teacher, school_class, subject: str):
        return assign_teacher_to_class_subject(db, teacher=teacher, school_class=school_class, subject=subject)
    
    def unassign_teacher_from_class_subject(self, db: Session, *, teacher, school_class, subject: str):
        return unassign_teacher_from_class_subject(db, teacher=teacher, school_class=school_class, subject=subject)
    
    def get_assignments_for_teacher(self, db: Session, *, teacher):
        return get_assignments_for_teacher(db, teacher=teacher)
    
    def get_teachers_for_class_subject(self, db: Session, *, school_class, subject: str):
        return get_teachers_for_class_subject(db, school_class=school_class, subject=subject)
    
    def get_teaching_staff_for_class(self, db: Session, *, school_class):
        return get_teaching_staff_for_class(db, school_class=school_class)
    
    def check_teacher_assigned_to_class_subject(self, db: Session, *, teacher, school_class, subject: str):
        return check_teacher_assigned_to_class_subject(db, teacher=teacher, school_class=school_class, subject=subject)


# Create the instance that will be imported
teacher_assignment = CRUDTeacherAssignment()
