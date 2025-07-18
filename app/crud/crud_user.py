from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.schemas.school_class import SchoolClass
from app.schemas.school_class import StudentAssignmentStatus
from typing import List


# -- READ Operations --

def get_user(db: Session, user_id: int) -> User | None:
    """
    Retrieve a single user by their ID.
    """
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> User | None:
    """
    Retrieve a single user by their email address.
    """
    return db.query(User).filter(User.email == email).first()

def get_user_by_roll_number(db: Session, roll_number: str) -> User | None:
    """
    Retrieve a single user by their roll number.
    """
    return db.query(User).filter(User.roll_number == roll_number).first()

def get_users(db: Session, skip: int = 0, limit: int = 100) -> list[User]:
    return db.query(User).order_by(User.roll_number).offset(skip).limit(limit).all() # Order by roll_number

# -- CREATE Operation --

def create_user(db: Session, *, user_in: UserCreate, password_hash: str) -> User:
    """
    Create a new user.
    'user_in' Pydantic schema now includes roll_number.
    Uniqueness of roll_number and email is handled by DB constraints.
    """
    # UserCreate now includes roll_number, email, full_name, role, is_active, is_superuser
    # Exclude 'password' as we handle its hashed version separately.
    db_user_data = user_in.model_dump(exclude={"password"})

    db_user = User(
        **db_user_data, # Unpacks roll_number, email, full_name, role, etc.
        hashed_password=password_hash
    )
    db.add(db_user)
    try:
        db.commit()
    except Exception as e: # Catch potential IntegrityError for unique constraints
        db.rollback()
        raise e
    db.refresh(db_user)
    return db_user


# -- UPDATE Operation --

def update_user(
    db: Session,
    *,
    db_user: User, # The existing User ORM model instance
    user_in: UserUpdate # Pydantic schema with fields to update (now includes optional roll_number)
) -> User:
    """
    Update an existing user.
    Uniqueness of roll_number and email (if changed) handled by DB constraints.
    """
    update_data = user_in.model_dump(exclude_unset=True)

    # Password update is handled by the API endpoint by hashing and setting db_user.hashed_password
    if "password" in update_data:
        # This CRUD function assumes password hashing is done by the caller (API endpoint)
        # and that the caller will set db_user.hashed_password directly if a new password is provided.
        # So, we remove 'password' from update_data to avoid trying to set a plain password field.
        del update_data["password"]

    for field, value in update_data.items():
        setattr(db_user, field, value)

    db.add(db_user)
    try:
        db.commit()
    except Exception as e: # Catch potential IntegrityError
        db.rollback()
        raise e
    db.refresh(db_user)
    return db_user


# -- DELETE Operations --
def remove_user(db: Session, *, db_user_to_delete: User) -> User: # Accepts User object
    """
    Delete a user object.
    The object should be fetched by the caller (e.g., by roll_number or id).
    Returns the deleted user object.
    """
    db.delete(db_user_to_delete)
    db.commit()
    return db_user_to_delete


# --- NEW: Student Enrollment CRUD ---

def assign_student_to_class(
        db: Session, *, student: User, school_class: SchoolClass
) -> User:
    """
    Assigns a student (User object) to a SchoolClass object.
    Updates the student's school_class_id.
    """
    if student.role != "student":
        # This is a business logic check, could also be in API layer
        raise ValueError("Only users with the 'student' role can be assigned to a class.")

    student.school_class_id = school_class.id
    # The student.enrolled_class relationship should also update,
    # but the FK is the source of truth.
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


def unassign_student_from_class(db: Session, *, student: User) -> User:
    """
    Unassigns a student (User object) from their current class.
    Sets the student's school_class_id to None.
    """
    if student.role != "student":
        raise ValueError("User is not a student, cannot unassign from class.")

    if student.school_class_id is None:
        # Student is already not assigned to any class
        return student  # Or raise an error/return a specific status

    student.school_class_id = None
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


def bulk_assign_students_to_class(
        db: Session,
        *,
        student_roll_numbers: List[str],
        target_school_class: SchoolClass
) -> List[StudentAssignmentStatus]:
    """
    Assigns a list of students (by roll number) to a target school class.
    Returns a list of status objects for each student.
    """
    results: List[StudentAssignmentStatus] = []
    students_to_commit: List[User] = []

    for roll_number in student_roll_numbers:
        student = get_user_by_roll_number(db, roll_number=roll_number)  # Assuming this exists

        # Initialize status for this student
        status_entry = StudentAssignmentStatus(
            student_roll_number=roll_number,
            status="processing",  # Default status, will be updated
            detail=""
        )

        if not student:
            status_entry.status = "error_student_not_found"
            status_entry.detail = f"Student with roll number '{roll_number}' not found."
        elif student.role != "student":
            status_entry.status = "error_not_a_student"
            status_entry.detail = f"User '{roll_number}' (Email: {student.email}) is not a student."
        elif student.school_class_id == target_school_class.id:
            status_entry.status = "already_in_this_class"
            status_entry.detail = f"Student '{roll_number}' is already enrolled in class '{target_school_class.class_code}'."
        elif student.school_class_id is not None:
            # Student is in another class, fetch its details
            conflicting_class = db.query(SchoolClass).filter(SchoolClass.id == student.school_class_id).first()
            conf_class_code = conflicting_class.class_code if conflicting_class else f"ID:{student.school_class_id}"
            status_entry.status = "error_already_in_another_class"
            status_entry.detail = f"Student '{roll_number}' is already enrolled in another class: '{conf_class_code}'. Must be unassigned first."
            status_entry.conflicting_class_code = conf_class_code
        else:
            # All checks passed, student can be assigned
            student.school_class_id = target_school_class.id
            students_to_commit.append(student)
            status_entry.status = "assigned"
            status_entry.detail = f"Student '{roll_number}' queued for assignment to class '{target_school_class.class_code}'."

        results.append(status_entry)

    if students_to_commit:
        try:
            db.add_all(students_to_commit)
            db.commit()
            for student_obj in students_to_commit:
                db.refresh(student_obj)
            # Update status for successfully committed students
            for res in results:
                if res.student_roll_number in [s.roll_number for s in students_to_commit] and res.status == "assigned":
                    res.detail = f"Student '{res.student_roll_number}' successfully assigned to class '{target_school_class.class_code}'."
        except Exception as e:
            db.rollback()
            # Update status for students that were meant to be committed but failed
            for res in results:
                if res.student_roll_number in [s.roll_number for s in
                                               students_to_commit] and res.status == "assigned":  # Check if it was one of the ones we tried to commit
                    res.status = "error_commit_failed"
                    res.detail = f"Database error during batch commit for student '{res.student_roll_number}': {str(e)}"

    return results


def bulk_unassign_students_from_class(
        db: Session,
        *,
        student_roll_numbers: List[str],
        source_school_class: SchoolClass  # The class students should be unassigned from
) -> List[StudentAssignmentStatus]:
    """
    Unassigns a list of students (by roll number) from a specific school class.
    Returns a list of status objects for each student.
    """
    results: List[StudentAssignmentStatus] = []
    students_to_commit: List[User] = []

    for roll_number in student_roll_numbers:
        student = get_user_by_roll_number(db, roll_number=roll_number)  # Assuming this exists

        status_entry = StudentAssignmentStatus(
            student_roll_number=roll_number,
            status="processing",
            detail=""
        )

        if not student:
            status_entry.status = "error_student_not_found"
            status_entry.detail = f"Student with roll number '{roll_number}' not found."
        elif student.role != "student":
            status_entry.status = "error_not_a_student"
            status_entry.detail = f"User '{roll_number}' (Email: {student.email}) is not a student."
        elif student.school_class_id is None:
            status_entry.status = "error_not_assigned_to_any_class"
            status_entry.detail = f"Student '{roll_number}' is not currently assigned to any class."
        elif student.school_class_id != source_school_class.id:
            # Student is in a class, but not the one specified for unassignment
            actual_class = db.query(SchoolClass).filter(SchoolClass.id == student.school_class_id).first()
            actual_class_code = actual_class.class_code if actual_class else f"ID:{student.school_class_id}"
            status_entry.status = "error_not_in_this_class"
            status_entry.detail = f"Student '{roll_number}' is enrolled in class '{actual_class_code}', not '{source_school_class.class_code}'. Cannot unassign from a class they are not in via this operation."
            status_entry.conflicting_class_code = actual_class_code
        else:
            # All checks passed, student can be unassigned from this class
            student.school_class_id = None
            students_to_commit.append(student)
            status_entry.status = "unassigned"
            status_entry.detail = f"Student '{roll_number}' queued for unassignment from class '{source_school_class.class_code}'."

        results.append(status_entry)

    if students_to_commit:
        try:
            db.add_all(students_to_commit)
            db.commit()
            for student_obj in students_to_commit:
                db.refresh(student_obj)
            # Update status for successfully committed students
            for res in results:
                if res.student_roll_number in [s.roll_number for s in
                                               students_to_commit] and res.status == "unassigned":
                    res.detail = f"Student '{res.student_roll_number}' successfully unassigned from class '{source_school_class.class_code}'."
        except Exception as e:
            db.rollback()
            for res in results:
                if res.student_roll_number in [s.roll_number for s in
                                               students_to_commit] and res.status == "unassigned":
                    res.status = "error_commit_failed"
                    res.detail = f"Database error during batch commit for student '{res.student_roll_number}': {str(e)}"

    return results


def search_students_for_teacher(
    db: Session,
    *,
    teacher_class_ids: List[int],
    name: str | None = None,
    roll_number: str | None = None,
    class_code: str | None = None,
) -> List[User]:
    """
    Searches for students within the classes a teacher is assigned to.
    """
    from app.models.school_class import SchoolClass as SchoolClassModel

    query = (
        db.query(User)
        .filter(User.role == "student")
        .filter(User.school_class_id.in_(teacher_class_ids))
    )

    if name:
        query = query.filter(User.full_name.ilike(f"%{name}%"))
    if roll_number:
        query = query.filter(User.roll_number == roll_number)
    if class_code:
        query = query.join(SchoolClassModel, User.school_class_id == SchoolClassModel.id).filter(SchoolClassModel.class_code == class_code)

    return query.all()
