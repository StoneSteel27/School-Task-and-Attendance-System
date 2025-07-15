from fastapi import APIRouter, Depends, HTTPException, status, Path, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from app import crud, models, schemas
from app.api import deps
from app.db.session import get_db

router = APIRouter()

# --- Teacher Task Endpoints ---

@router.post(
    "/classes/{class_code}/tasks",
    response_model=schemas.Task,
    status_code=status.HTTP_201_CREATED,
    summary="Teacher: Create a new task for a specific class and subject"
)
def create_task_for_class(
    class_code: str,
    task_in: schemas.TaskCreate,
    db: Session = Depends(get_db),
    current_teacher: models.User = Depends(deps.get_current_active_user)
):
    """
    Allows a teacher to create a new task for a specific class and subject.
    The teacher must be assigned to teach the specified subject in that class.
    """
    if current_teacher.role != "teacher":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only teachers can create tasks.")

    db_class = crud.crud_school_class.get_school_class_orm_by_class_code(db, class_code=class_code)
    if not db_class:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Class with code '{class_code}' not found.")

    # Verify the teacher is assigned to teach this subject in this class
    is_assigned = crud.crud_teacher_assignment.check_teacher_assigned_to_class_subject(
        db=db, teacher=current_teacher, school_class=db_class, subject=task_in.subject
    )
    if not is_assigned:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Teacher is not assigned to teach '{task_in.subject}' in class '{class_code}'."
        )

    try:
        task = crud.crud_task.create_task(
            db=db,
            task_in=task_in,
            school_class_id=db_class.id,
            created_by_teacher_id=current_teacher.id
        )
        return task
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to create task: {str(e)}")


@router.get(
    "/classes/{class_code}/tasks",
    response_model=List[schemas.Task],
    summary="Teacher: Get all tasks for a specific class and optionally filter by subject"
)
def get_tasks_for_class_by_teacher(
    class_code: str,
    subject: Optional[str] = Query(None, description="Filter tasks by subject."),
    db: Session = Depends(get_db),
    current_teacher: models.User = Depends(deps.get_current_active_user)
):
    """
    Allows a teacher to retrieve tasks for a specific class they are assigned to.
    Can filter by subject.
    """
    if current_teacher.role != "teacher":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only teachers can view tasks for classes they teach.")

    db_class = crud.crud_school_class.get_school_class_orm_by_class_code(db, class_code=class_code)
    if not db_class:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Class with code '{class_code}' not found.")

    # Verify the teacher is assigned to teach *any* subject in this class, or a specific subject if filtered
    # For simplicity, we'll allow viewing if they teach *any* subject in the class.
    # A more strict check would be to ensure they teach the 'subject' if it's provided.
    teacher_assignments = crud.crud_teacher_assignment.get_assignments_for_teacher(db, teacher=current_teacher)
    teacher_class_subjects = {(assign['school_class_code'], assign['subject']) for assign in teacher_assignments}

    is_teacher_for_class = False
    if subject:
        if (class_code, subject) in teacher_class_subjects:
            is_teacher_for_class = True
    else:
        # Check if teacher teaches any subject in this class
        if any(assign_class_code == class_code for assign_class_code, _ in teacher_class_subjects):
            is_teacher_for_class = True

    if not is_teacher_for_class:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Teacher is not assigned to teach in class '{class_code}' or for the specified subject."
        )

    tasks = crud.crud_task.get_tasks_for_class(db, school_class_id=db_class.id)
    if subject:
        tasks = [task for task in tasks if task.subject == subject]

    return tasks


@router.put(
    "/tasks/{task_id}",
    response_model=schemas.Task,
    summary="Teacher: Update an existing task"
)
def update_task_by_teacher(
    task_id: int,
    task_in: schemas.TaskUpdate,
    db: Session = Depends(get_db),
    current_teacher: models.User = Depends(deps.get_current_active_user)
):
    """
    Allows a teacher to update a task they created.
    """
    if current_teacher.role != "teacher":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only teachers can update tasks.")

    db_task = crud.crud_task.get_task(db, task_id=task_id)
    if not db_task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found.")

    if db_task.created_by_teacher_id != current_teacher.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not authorized to update this task.")

    # If subject is being updated, ensure the teacher is assigned to the new subject in the same class
    if task_in.subject and task_in.subject != db_task.subject:
        db_class = crud.crud_school_class.get_school_class_orm_by_id(db, class_id=db_task.school_class_id)
        if not db_class:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Associated class not found for task.")

        is_assigned_to_subject = crud.crud_teacher_assignment.check_teacher_assigned_to_class_subject(
            db=db, teacher=current_teacher, school_class=db_class, subject=task_in.subject
        )
        if not is_assigned_to_subject:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"You are not assigned to teach '{task_in.subject}' in class '{db_class.class_code}'."
            )

    try:
        updated_task = crud.crud_task.update_task(db=db, db_task=db_task, task_in=task_in)
        return updated_task
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to update task: {str(e)}")


@router.delete(
    "/tasks/{task_id}",
    response_model=schemas.Task,
    summary="Teacher: Delete a task"
)
def delete_task_by_teacher(
    task_id: int,
    db: Session = Depends(get_db),
    current_teacher: models.User = Depends(deps.get_current_active_user)
):
    """
    Allows a teacher to delete a task they created.
    """
    if current_teacher.role != "teacher":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only teachers can delete tasks.")

    db_task = crud.crud_task.get_task(db, task_id=task_id)
    if not db_task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found.")

    if db_task.created_by_teacher_id != current_teacher.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not authorized to delete this task.")

    try:
        deleted_task = crud.crud_task.delete_task(db=db, task_id=task_id)
        return deleted_task
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to delete task: {str(e)}")


# --- Teacher Announcement Endpoints ---

@router.post(
    "/announcements",
    response_model=schemas.Announcement,
    status_code=status.HTTP_201_CREATED,
    summary="Teacher: Create a new announcement (class-specific or subject-specific)"
)
def create_announcement_by_teacher(
    announcement_in: schemas.AnnouncementCreate,
    db: Session = Depends(get_db),
    current_teacher: models.User = Depends(deps.get_current_active_user)
):
    """
    Allows a teacher to create a new announcement. 
    Announcements can be class-specific or subject-specific within a class.
    Teachers cannot create school-wide announcements.
    """
    if current_teacher.role != "teacher":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only teachers can create announcements.")

    if announcement_in.is_school_wide:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Teachers cannot create school-wide announcements.")

    if announcement_in.school_class_id:
        db_class = crud.crud_school_class.get_school_class_orm_by_id(db, class_id=announcement_in.school_class_id)
        if not db_class:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Class with ID '{announcement_in.school_class_id}' not found.")
        
        # Verify teacher is assigned to this class (any subject) or specific subject if provided
        teacher_assignments = crud.crud_teacher_assignment.get_assignments_for_teacher(db, teacher=current_teacher)
        teacher_class_codes = {assign['school_class_code'] for assign in teacher_assignments}
        
        if db_class.class_code not in teacher_class_codes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Teacher is not assigned to teach in class '{db_class.class_code}'."
            )
        
        if announcement_in.subject:
            is_assigned_to_subject = crud.crud_teacher_assignment.check_teacher_assigned_to_class_subject(
                db=db, teacher=current_teacher, school_class=db_class, subject=announcement_in.subject
            )
            if not is_assigned_to_subject:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"You are not assigned to teach '{announcement_in.subject}' in class '{db_class.class_code}'."
                )

    else:
        # If not school_class_id, it implies a school-wide announcement, which is forbidden for teachers.
        # This case should ideally be caught by the is_school_wide check above, but as a safeguard.
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Announcements must be associated with a class or be school-wide (not allowed for teachers).")

    try:
        announcement = crud.crud_announcement.create_announcement(
            db=db,
            announcement_in=announcement_in,
            created_by_user_id=current_teacher.id
        )
        return announcement
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to create announcement: {str(e)}")


@router.get(
    "/classes/{class_code}/announcements",
    response_model=List[schemas.Announcement],
    summary="Teacher: Get class-specific announcements, optionally filtered by subject"
)
def get_class_announcements_by_teacher(
    class_code: str,
    subject: Optional[str] = Query(None, description="Filter announcements by subject."),
    db: Session = Depends(get_db),
    current_teacher: models.User = Depends(deps.get_current_active_user)
):
    """
    Allows a teacher to retrieve class-specific announcements for a class they are assigned to.
    Can filter by subject.
    """
    if current_teacher.role != "teacher":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only teachers can view class announcements.")

    db_class = crud.crud_school_class.get_school_class_orm_by_class_code(db, class_code=class_code)
    if not db_class:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Class with code '{class_code}' not found.")

    # Verify the teacher is assigned to teach in this class (any subject) or specific subject if filtered
    teacher_assignments = crud.crud_teacher_assignment.get_assignments_for_teacher(db, teacher=current_teacher)
    teacher_class_subjects = {(assign['school_class_code'], assign['subject']) for assign in teacher_assignments}

    is_teacher_for_class = False
    if subject:
        if (class_code, subject) in teacher_class_subjects:
            is_teacher_for_class = True
    else:
        if any(assign_class_code == class_code for assign_class_code, _ in teacher_class_subjects):
            is_teacher_for_class = True

    if not is_teacher_for_class:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Teacher is not assigned to teach in class '{class_code}' or for the specified subject."
        )

    if subject:
        announcements = crud.crud_announcement.get_subject_announcements_for_class(db, school_class_id=db_class.id, subject=subject)
    else:
        announcements = crud.crud_announcement.get_class_announcements(db, school_class_id=db_class.id)
    
    return announcements


@router.put(
    "/announcements/{announcement_id}",
    response_model=schemas.Announcement,
    summary="Teacher: Update an existing announcement"
)
def update_announcement_by_teacher(
    announcement_id: int,
    announcement_in: schemas.AnnouncementUpdate,
    db: Session = Depends(get_db),
    current_teacher: models.User = Depends(deps.get_current_active_user)
):
    """
    Allows a teacher to update an announcement they created.
    Teachers cannot change an announcement to be school-wide.
    """
    if current_teacher.role != "teacher":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only teachers can update announcements.")

    db_announcement = crud.crud_announcement.get_announcement(db, announcement_id=announcement_id)
    if not db_announcement:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Announcement not found.")

    if db_announcement.created_by_user_id != current_teacher.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not authorized to update this announcement.")

    if announcement_in.is_school_wide is True and not db_announcement.is_school_wide:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Teachers cannot change an announcement to be school-wide.")

    # If school_class_id or subject is being updated, ensure teacher is assigned to the new context
    if announcement_in.school_class_id and announcement_in.school_class_id != db_announcement.school_class_id:
        db_class = crud.crud_school_class.get_school_class_orm_by_id(db, class_id=announcement_in.school_class_id)
        if not db_class:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"New class with ID '{announcement_in.school_class_id}' not found.")
        
        teacher_assignments = crud.crud_teacher_assignment.get_assignments_for_teacher(db, teacher=current_teacher)
        teacher_class_codes = {assign['school_class_code'] for assign in teacher_assignments}
        
        if db_class.class_code not in teacher_class_codes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Teacher is not assigned to teach in the new class '{db_class.class_code}'."
            )

    if announcement_in.subject and announcement_in.subject != db_announcement.subject:
        if not db_announcement.school_class_id and not announcement_in.school_class_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot change subject for a school-wide announcement without specifying a class.")
        
        target_class_id = announcement_in.school_class_id if announcement_in.school_class_id else db_announcement.school_class_id
        db_class = crud.crud_school_class.get_school_class_orm_by_id(db, class_id=target_class_id)
        if not db_class:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Associated class not found for announcement.")

        is_assigned_to_subject = crud.crud_teacher_assignment.check_teacher_assigned_to_class_subject(
            db=db, teacher=current_teacher, school_class=db_class, subject=announcement_in.subject
        )
        if not is_assigned_to_subject:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"You are not assigned to teach '{announcement_in.subject}' in class '{db_class.class_code}'."
            )

    try:
        updated_announcement = crud.crud_announcement.update_announcement(db=db, db_announcement=db_announcement, announcement_in=announcement_in)
        return updated_announcement
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to update announcement: {str(e)}")


@router.delete(
    "/announcements/{announcement_id}",
    response_model=schemas.Announcement,
    summary="Teacher: Delete an announcement"
)
def delete_announcement_by_teacher(
    announcement_id: int,
    db: Session = Depends(get_db),
    current_teacher: models.User = Depends(deps.get_current_active_user)
):
    """
    Allows a teacher to delete an announcement they created.
    """
    if current_teacher.role != "teacher":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only teachers can delete announcements.")

    db_announcement = crud.crud_announcement.get_announcement(db, announcement_id=announcement_id)
    if not db_announcement:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Announcement not found.")

    if db_announcement.created_by_user_id != current_teacher.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not authorized to delete this announcement.")

    try:
        deleted_announcement = crud.crud_announcement.delete_announcement(db=db, announcement_id=announcement_id)
        return deleted_announcement
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to delete announcement: {str(e)}")
