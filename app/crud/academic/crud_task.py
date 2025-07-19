from datetime import date
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError

from app.models.academic.task import Task, TaskStatus, StudentTaskSubmission # Import the Task model, TaskStatus enum, and StudentTaskSubmission
from app.models.auth.user import User # For relationships
from app.models.core.school_class import SchoolClass # For relationships
from app.schemas.academic.task import TaskCreate, TaskUpdate, StudentTaskSubmissionCreate, StudentTaskSubmissionUpdate # Import Pydantic schemas


def get_task(db: Session, task_id: int) -> Optional[Task]:
    """Retrieve a single task by its ID."""
    return (
        db.query(Task)
        .options(
            joinedload(Task.created_by_teacher),
            joinedload(Task.school_class)
        )
        .filter(Task.id == task_id)
        .first()
    )


def get_tasks_for_class(db: Session, school_class_id: int, student_id: int = None, skip: int = 0, limit: int = 100) -> List[Task]:
    """Retrieve all tasks for a specific school class."""
    query = (
        db.query(Task, StudentTaskSubmission.status, StudentTaskSubmission.submission_url, StudentTaskSubmission.submitted_at)
        .outerjoin(StudentTaskSubmission, (Task.id == StudentTaskSubmission.task_id) & (StudentTaskSubmission.student_id == student_id))
        .options(
            joinedload(Task.created_by_teacher)
        )
        .filter(Task.school_class_id == school_class_id)
        .order_by(Task.due_date.asc(), Task.created_at.desc())
    )

    results = query.offset(skip).limit(limit).all()

    tasks = []
    for task, status, submission_url, submitted_at in results:
        task.submission_status = status
        task.submission_url = submission_url
        task.submitted_at = submitted_at
        tasks.append(task)

    return tasks



def get_tasks_created_by_teacher(db: Session, teacher_id: int, skip: int = 0, limit: int = 100) -> List[Task]:
    """Retrieve all tasks created by a specific teacher."""
    return (
        db.query(Task)
        .options(
            joinedload(Task.school_class)
        )
        .filter(Task.created_by_teacher_id == teacher_id)
        .order_by(Task.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_task(db: Session, *, task_in: TaskCreate, school_class_id: int, created_by_teacher_id: int) -> Task:
    """Create a new task."""
    db_task = Task(
        **task_in.model_dump(),
        school_class_id=school_class_id,
        created_by_teacher_id=created_by_teacher_id
    )
    db.add(db_task)
    try:
        db.commit()
        db.refresh(db_task)
    except IntegrityError as e:
        db.rollback()
        raise IntegrityError(f"Database integrity error while creating task: {e.orig}", e.params, e.orig) from e
    except Exception as e:
        db.rollback()
        raise e
    return db_task


def update_task(db: Session, *, db_task: Task, task_in: TaskUpdate) -> Task:
    """Update an existing task."""
    update_data = task_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_task, field, value)

    db.add(db_task)
    try:
        db.commit()
        db.refresh(db_task)
    except IntegrityError as e:
        db.rollback()
        raise IntegrityError(f"Database integrity error while updating task: {e.orig}", e.params, e.orig) from e
    except Exception as e:
        db.rollback()
        raise e
    return db_task


def get_student_task_submission(db: Session, task_id: int, student_id: int) -> Optional[StudentTaskSubmission]:
    """Retrieve a student's submission for a specific task."""
    return db.query(StudentTaskSubmission).filter(
        StudentTaskSubmission.task_id == task_id,
        StudentTaskSubmission.student_id == student_id
    ).first()


def create_or_update_student_task_submission(
    db: Session,
    *,
    task_id: int,
    student_id: int,
    submission_url: str,
    status: TaskStatus = TaskStatus.SUBMITTED
) -> StudentTaskSubmission:
    """
    Create a new student task submission or update an existing one.
    If a submission for the given task_id and student_id already exists, it updates it.
    Otherwise, it creates a new submission.
    """
    db_submission = get_student_task_submission(db, task_id, student_id)

    if db_submission:
        # Update existing submission
        db_submission.submission_url = submission_url
        db_submission.status = status
    else:
        # Create new submission
        db_submission = StudentTaskSubmission(
            task_id=task_id,
            student_id=student_id,
            submission_url=submission_url,
            status=status
        )
        db.add(db_submission)
    
    try:
        db.commit()
        db.refresh(db_submission)
    except IntegrityError as e:
        db.rollback()
        raise IntegrityError(f"Database integrity error while creating/updating student task submission: {e.orig}", e.params, e.orig) from e
    except Exception as e:
        db.rollback()
        raise e
    return db_submission


def delete_task(db: Session, *, task_id: int) -> Optional[Task]:
    """Delete a task by its ID."""
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if db_task:
        db.delete(db_task)
        db.commit()
    return db_task


# Create a simple object to provide access to all task CRUD functions
class CRUDTask:
    """CRUD operations for Task and StudentTaskSubmission models"""

    def get(self, db: Session, task_id: int):
        return get_task(db, task_id)

    def get_tasks_for_class(self, db: Session, school_class_id: int, student_id=None, skip=0, limit=100):
        return get_tasks_for_class(db, school_class_id, student_id, skip, limit)

    def get_tasks_created_by_teacher(self, db: Session, teacher_id: int, skip=0, limit=100):
        return get_tasks_created_by_teacher(db, teacher_id, skip, limit)

    def create(self, db: Session, *, obj_in, school_class_id: int, created_by_teacher_id: int):
        return create_task(db, task_in=obj_in, school_class_id=school_class_id, created_by_teacher_id=created_by_teacher_id)

    def update(self, db: Session, *, db_obj, obj_in):
        return update_task(db, db_task=db_obj, task_in=obj_in)

    def delete(self, db: Session, *, task_id: int):
        return delete_task(db, task_id=task_id)

    def get_student_submission(self, db: Session, task_id: int, student_id: int):
        return get_student_task_submission(db, task_id, student_id)

    def create_or_update_student_submission(self, db: Session, *, task_id: int, student_id: int, submission_url: str, status=None):
        return create_or_update_student_task_submission(db, task_id=task_id, student_id=student_id, submission_url=submission_url, status=status)


# Create the instance that will be imported
task = CRUDTask()
