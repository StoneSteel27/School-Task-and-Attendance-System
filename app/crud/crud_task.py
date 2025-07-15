from datetime import date
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError

from app.models.task import Task, TaskStatus # Import the Task model and TaskStatus enum
from app.models.user import User # For relationships
from app.models.school_class import SchoolClass # For relationships
from app.schemas.task import TaskCreate, TaskUpdate # Import Pydantic schemas


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


def get_tasks_for_class(db: Session, school_class_id: int, skip: int = 0, limit: int = 100) -> List[Task]:
    """Retrieve all tasks for a specific school class."""
    return (
        db.query(Task)
        .options(
            joinedload(Task.created_by_teacher)
        )
        .filter(Task.school_class_id == school_class_id)
        .order_by(Task.due_date.asc(), Task.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


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


def delete_task(db: Session, *, task_id: int) -> Optional[Task]:
    """Delete a task by its ID."""
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if db_task:
        db.delete(db_task)
        db.commit()
    return db_task
