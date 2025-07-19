from typing import List, Optional
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app import crud, models
from app.api import deps
from app.db.session import get_db
from app.schemas.core.schedule import ClassScheduleSlot
from app.schemas.academic.task import Task, StudentTaskSubmission
from app.schemas.academic.announcement import Announcement, AnnouncementCreate
from app.schemas.core.school_class import ClassTeachingStaffDetail, TeacherTeachingDetail

router = APIRouter()


@router.get("/me/classes", response_model=List[ClassTeachingStaffDetail])
def get_my_classes(
    db: Session = Depends(get_db),
    current_teacher: models.User = Depends(deps.get_current_active_teacher),
):
    """
    Get the list of classes that the current teacher is assigned to.
    Accessible by the teacher themselves.
    """
    return crud.crud_teacher_assignment.get_classes_for_teacher(db=db, teacher=current_teacher)


@router.get(
    "/{teacher_roll_number}/teaching-load",
    response_model=List[TeacherTeachingDetail]
)
def get_teacher_teaching_load_endpoint(
    # teacher_roll_number is handled by the dependency
    db: Session = Depends(get_db),
    # REPLACED: current_user: models.User = Depends(deps.get_current_active_user)
    # WITH:
    db_teacher: models.User = Depends(deps.get_teacher_for_view_permission) # NEW Dependency
):
    """
    Get the list of classes and subjects a specific teacher (by teacher_roll_number in path) is assigned to teach.
    Accessible by the teacher themselves or a superuser (enforced by get_teacher_for_view_permission).
    """
    # db_teacher is the authorized teacher ORM object.
    # Role check (role == "teacher") is also handled by the dependency.

    assignments = crud.crud_teacher_assignment.get_assignments_for_teacher(db=db, teacher=db_teacher)
    return assignments

@router.get(
    "/me/schedule",
    response_model=List[ClassScheduleSlot],
    summary="Get Current Teacher's Schedule"
)
def get_teacher_schedule(
        target_date: Optional[date] = Query(None,
                                            description="If provided, returns the schedule for this specific date. Otherwise, weekly template based on day_of_week or all."),
        day_of_week: Optional[int] = Query(None,
                                           description="Filter by specific day of the week (0=Monday, 6=Sunday). Used if target_date is not provided.",
                                           ge=0, le=6),
        db: Session = Depends(get_db),
        current_teacher: models.User = Depends(deps.get_current_active_teacher)
):
    """
    Get the schedule for a specific teacher (by teacher_roll_number in path).
    - Access: Teacher themselves or a Superuser (enforced by get_teacher_for_view_permission).
    """
    # current_teacher is the authorized teacher ORM object.

    if target_date and day_of_week is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot specify both 'target_date' and 'day_of_week'."
        )

    slots_to_return_orm: List[models.ClassScheduleSlot] = []

    if target_date:
        day_of_week_from_date = target_date.weekday()
        potential_slots_for_day_orm = crud.crud_schedule.get_schedule_slots_for_teacher(
            db, teacher_id=current_teacher.id, day_of_week=day_of_week_from_date
        ) # This crud already eager loads school_class
        for slot_orm in potential_slots_for_day_orm:
            if not slot_orm.school_class:
                continue # Should ideally not happen
            active_holidays = crud.crud_schedule.get_holidays_active_on_date(
                db=db, target_date=target_date, grade_filter_value=slot_orm.school_class.grade
            )
            if not active_holidays:
                slots_to_return_orm.append(slot_orm)
    elif day_of_week is not None:
        slots_to_return_orm = crud.crud_schedule.get_schedule_slots_for_teacher(
            db, teacher_id=current_teacher.id, day_of_week=day_of_week
        ) # This crud already eager loads school_class
    else:
        slots_to_return_orm = crud.crud_schedule.get_schedule_slots_for_teacher(db, teacher_id=current_teacher.id)
        # This crud already eager loads school_class

    return slots_to_return_orm

@router.get("/me/tasks", response_model=List[Task])
def get_tasks_created_by_me(
    db: Session = Depends(get_db),
    current_teacher: models.User = Depends(deps.get_current_active_teacher),
):
    """
    Get the list of tasks created by the current teacher.
    Accessible by the teacher themselves.
    """
    return crud.crud_task.get_tasks_by_creator(db=db, creator=current_teacher)


@router.post("/me/announcements", response_model=Announcement)
def create_announcement_for_my_class(
    announcement_in: AnnouncementCreate,
    db: Session = Depends(get_db),
    current_teacher: models.User = Depends(deps.get_current_active_teacher),
):
    """
    Create a new announcement for the class(es) you are teaching.
    Accessible by the teacher themselves.
    """
    # The dependency ensures the teacher is active and authorized.
    return crud.crud_announcement.create_announcement_for_teacher_classes(
        db=db, announcement_in=announcement_in, teacher=current_teacher
    )


@router.get(
    "/me/tasks/{task_id}/submissions",
    response_model=List[StudentTaskSubmission],
    summary="Get Submissions for a Task Created by the Teacher"
)
def get_submissions_for_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_teacher: models.User = Depends(deps.get_current_active_teacher),
):
    """
    Get all submissions for a specific task that you have created.
    Accessible by the teacher themselves.
    """
    return crud.crud_task_submission.get_submissions_by_task_and_teacher(
        db=db, task_id=task_id, teacher_id=current_teacher.id
    )


@router.put(
    "/me/submissions/{submission_id}/approve",
    response_model=StudentTaskSubmission,
    summary="Approve a Task Submission"
)
def approve_submission(
    submission_id: int,
    db: Session = Depends(get_db),
    current_teacher: models.User = Depends(deps.get_current_active_teacher),
):
    """
    Approve a task submission from a student.
    Accessible by the teacher themselves.
    """
    return crud.crud_task_submission.approve_submission_by_teacher(
        db=db, submission_id=submission_id, teacher_id=current_teacher.id
    )
