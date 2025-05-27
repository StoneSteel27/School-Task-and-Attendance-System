from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps # deps will now contain get_student_for_view_permission
from app.db.session import get_db

router = APIRouter()

@router.get(
    "/{student_roll_number}/schedule",
    response_model=List[schemas.ClassScheduleSlot],
    summary="Get Student's Class Schedule"
)
def get_student_schedule(
        # student_roll_number is now handled by the dependency
        target_date: Optional[date] = Query(None,
                                            description="If provided, returns the schedule for this specific date for the student's class, considering holidays. Otherwise, returns the weekly class schedule template."),
        db: Session = Depends(get_db),
        # REPLACED: current_user: models.User = Depends(deps.get_current_active_user)
        # WITH:
        db_student: models.User = Depends(deps.get_student_for_view_permission) # NEW Dependency
):
    """
    Get the schedule for a specific student (identified by student_roll_number in path).
    This is effectively the schedule of the class the student is enrolled in.
    - If `target_date` is provided, it shows the schedule for that day,
      returning an empty list if it's a holiday for the student's class grade.
    - If `target_date` is omitted, it returns the full weekly schedule template for the class.
    - Access: Student themselves or a Superuser (enforced by get_student_for_view_permission).
    """
    # The old logic for fetching student by roll_number, checking if exists,
    # checking role, and authorization is now handled by deps.get_student_for_view_permission.
    # db_student is the authorized student ORM object.

    if db_student.school_class_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student is not currently enrolled in any class, so no schedule is available."
        )

    # db_student.enrolled_class should be the SchoolClass ORM object if relationships are set up.
    # However, to be safe or if you only need the ID and grade, fetching directly might be preferred
    # if `enrolled_class` is not always eagerly loaded or available.
    # Let's assume `db_student.enrolled_class` gives us the necessary `SchoolClass` object.
    # If not, we would fetch it:
    db_student_class = db_student.enrolled_class
    if not db_student_class: # Fallback if enrolled_class relationship isn't populated as expected
         db_student_class = crud.crud_school_class.get_school_class_orm_by_id(db, class_id=db_student.school_class_id)

    if not db_student_class:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, # Or 404 if class became unlinked
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