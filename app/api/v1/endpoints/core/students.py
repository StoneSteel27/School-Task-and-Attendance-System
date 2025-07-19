from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status, Path, UploadFile, File
from sqlalchemy.orm import Session
import shutil
import os

from app import crud, models
from app.crud.academic import crud_task
from app.api import deps
from app.db.session import get_db
from app.schemas.core.subject import Subject
from app.crud.core import subject as crud_subject
from app.schemas.core.schedule import ClassScheduleSlot
from app.schemas.attendance.student_attendance import StudentAttendanceRecord
from app.schemas.academic.task import TaskWithSubmissionStatus, StudentTaskSubmission
from app.models.academic.task import TaskStatus
from app.schemas.academic.announcement import Announcement

router = APIRouter()

SUBMISSIONS_DIR = "submissions"


# Ensure the submissions directory exists
if not os.path.exists(SUBMISSIONS_DIR):
    os.makedirs(SUBMISSIONS_DIR)

@router.get(
    "/me/schedule",
    response_model=List[ClassScheduleSlot],
    summary="Get Student's Class Schedule"
)
def get_student_schedule(
        target_date: Optional[date] = Query(None,
                                            description="If provided, returns the schedule for this specific date for the student's class, considering holidays. Otherwise, returns the weekly class schedule template."),
        db: Session = Depends(get_db),
        current_user: models.User = Depends(deps.get_current_active_user)
):
    """
    Get the schedule for the current student.
    - If `target_date` is provided, it shows the schedule for that day,
      returning an empty list if it's a holiday for the student's class grade.
    - If `target_date` is omitted, it returns the full weekly schedule template for the class.
    - Access: Student themselves.
    """
    if current_user.role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can access this schedule."
        )
    db_student = current_user

    if db_student.school_class_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student is not currently enrolled in any class, so no schedule is available."
        )

    db_student_class = db_student.enrolled_class
    if not db_student_class:
         db_student_class = crud.crud_school_class.get_school_class_orm_by_id(db, class_id=db_student.school_class_id)

    if not db_student_class:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not retrieve class details for the student. Class may be missing or unlinked."
        )

    weekly_slots_orm = crud.crud_schedule.get_schedule_slots_for_class(db=db,
                                                                       school_class_id=db_student.school_class_id)

    if target_date:
        active_holidays = crud.crud_schedule.get_holidays_active_on_date(
            db=db, target_date=target_date, grade_filter_value=db_student_class.grade
        )
        if active_holidays:
            return []

        target_day_of_week = target_date.weekday()
        daily_schedule_slots = [
            slot for slot in weekly_slots_orm if slot.day_of_week == target_day_of_week
        ]
        return daily_schedule_slots
    else:
        return weekly_slots_orm

@router.get(
    "/me/attendance",
    response_model=List[StudentAttendanceRecord],
    summary="Get Student's Attendance Records over a Date Range"
)
def get_student_attendance_records_range(
    start_date_str: str = Query(..., alias="startDate", description="Start date in YYYY-MM-DD format."),
    end_date_str: str = Query(..., alias="endDate", description="End date in YYYY-MM-DD format."),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_user)
):
    """
    Retrieve attendance records for the current student over a given date range.
    Accessible by the student themselves.
    """
    if current_user.role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can access attendance records."
        )
    target_student = current_user

    try:
        start_date = date.fromisoformat(start_date_str)
        end_date = date.fromisoformat(end_date_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format. Use YYYY-MM-DD for startDate and endDate."
        )

    if end_date < start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="End date cannot be before start date."
        )

    attendance_orm_list = crud.crud_student_attendance.get_attendance_for_student_date_range(
        db=db,
        student_id=target_student.id,
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=limit
    )
    return attendance_orm_list


@router.get(
    "/me/tasks",
    response_model=List[TaskWithSubmissionStatus],
    summary="Get Student's Tasks"
)
def get_student_tasks(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_user)
):
    """
    Retrieve all tasks assigned to the current student's class.
    Accessible by the student themselves.
    """
    if current_user.role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can access tasks."
        )
    db_student = current_user

    if db_student.school_class_id is None:
        return []
    
    tasks = crud.crud_task.get_tasks_for_class(db, school_class_id=db_student.school_class_id, student_id=db_student.id)
    return tasks



@router.get(
    "/me/announcements",
    response_model=List[Announcement],
    summary="Get Student's Announcements (School-wide, Class-specific, Subject-specific)"
)
def get_student_announcements(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_user)
):
    """
    Retrieve all announcements relevant to the current student:
    - School-wide announcements.
    - Class-specific announcements for their enrolled class.
    - Subject-specific announcements for their enrolled class.
    Accessible by the student themselves.
    """
    if current_user.role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can access announcements."
        )
    db_student = current_user
    announcements: List[schemas.Announcement] = []

    # 1. Get school-wide announcements
    school_wide_announcements = crud.crud_announcement.get_school_wide_announcements(db)
    announcements.extend(school_wide_announcements)

    # 2. Get class-specific and subject-specific announcements if student is enrolled in a class
    if db_student.school_class_id:
        db_student_class = db_student.enrolled_class
        if not db_student_class:
            # Fallback if enrolled_class relationship isn't populated as expected
            db_student_class = crud.crud_school_class.get_school_class_orm_by_id(db, class_id=db_student.school_class_id)

        if db_student_class:
            # Get class-specific announcements
            class_announcements = crud.crud_announcement.get_class_announcements(db, school_class_id=db_student_class.id)
            announcements.extend(class_announcements)

            # Get subject-specific announcements for all subjects taught in this class
            # This requires knowing what subjects are taught in the class, which might be complex.
            # For simplicity, let's assume we can get all announcements for the class and filter by subject later if needed.
            # Or, if subjects are explicitly linked to students, we could filter by those.
            # For now, the `get_class_announcements` already covers non-school-wide announcements for the class.
            # If we need to fetch by subject, we'd need to know the subjects the student is taking.
            # Given the current schema, a student is in a class, and tasks/announcements are for a class/subject.
            # The `get_class_announcements` should suffice for now, as it fetches all non-school-wide for the class.
            pass # No additional CRUD call needed for subject-specific if get_class_announcements is broad enough

    # Remove duplicates if any (e.g., if an announcement is mistakenly marked both school-wide and class-specific)
    # This is a simple deduplication based on ID, assuming Announcement objects are hashable or comparable by ID.
    unique_announcements = {announcement.id: announcement for announcement in announcements}.values()
    return list(unique_announcements)


@router.post(
    "/me/tasks/{task_id}/submit",
    response_model=StudentTaskSubmission,
    summary="Submit a file for a student's task"
)
async def submit_task_file(
    task_id: int = Path(..., description="The ID of the task to submit for."),
    file: UploadFile = File(..., description="The file to upload for the task submission."),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_user) # Ensures student is authorized
):
    """
    Allows a student to submit a file for a specific task.
    - The file will be saved to the `submissions/` directory.
    - The submission URL and status will be updated in the database.
    - Accessible by the student themselves.
    """
    # Verify the user is a student
    if current_user.role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can submit tasks."
        )
    db_student = current_user

    # Verify the task exists and is assigned to the student's class
    task = crud.crud_task.get_task(db, task_id=task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found."
        )
    
    if task.school_class_id != db_student.school_class_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Task is not assigned to this student's class."
        )

    # Generate a unique filename
    # Using student_id, task_id, and original filename to ensure uniqueness and traceability
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"task_{task_id}_student_{db_student.id}_{os.urandom(8).hex()}{file_extension}"
    file_path = os.path.join(SUBMISSIONS_DIR, unique_filename)

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not upload file: {e}"
        )
    finally:
        file.file.close()

    # Update or create the student's task submission record
    try:
        db_submission = crud_task.create_or_update_student_task_submission(
            db=db,
            task_id=task_id,
            student_id=db_student.id,
            submission_url=file_path, # Store the local path
            status=TaskStatus.SUBMITTED # Set status to submitted
        )
        return db_submission
    except Exception as e:
        # If database update fails, try to clean up the uploaded file
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not update task submission in database: {e}"
        )


@router.get("/me/subjects", response_model=List[Subject])
def list_student_subjects(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """
    Get a list of subjects for the current student's class.
    """
    if current_user.role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can view their subjects.",
        )

    if not current_user.school_class_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student is not enrolled in any class.",
        )

    subjects = crud_subject.get_subjects_by_class(db, class_id=current_user.school_class_id)
    return subjects
