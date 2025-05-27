from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app import crud, models, schemas  # Make sure these are imported correctly
from app.api import deps
from app.db.session import get_db

router = APIRouter()


@router.get(
    "/{student_roll_number}/schedule",
    response_model=List[schemas.ClassScheduleSlot],
    summary="Get Student's Class Schedule"
)
def get_student_schedule(
        student_roll_number: str,
        target_date: Optional[date] = Query(None,
                                            description="If provided, returns the schedule for this specific date for the student's class, considering holidays. Otherwise, returns the weekly class schedule template."),
        db: Session = Depends(get_db),
        current_user: models.User = Depends(deps.get_current_active_user)
):
    """
    Get the schedule for a specific student.
    This is effectively the schedule of the class the student is enrolled in.
    - If `target_date` is provided, it shows the schedule for that day,
      returning an empty list if it's a holiday for the student's class grade.
    - If `target_date` is omitted, it returns the full weekly schedule template for the class.
    - Access: Student themselves or a Superuser.
    """
    db_student = crud.crud_user.get_user_by_roll_number(db, roll_number=student_roll_number)

    if not db_student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found."
        )

    if db_student.role != "student":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User with roll number {student_roll_number} is not a student."
        )

    # Authorization: Student can see their own schedule, Superuser can see any student's schedule
    if not (current_user.id == db_student.id or current_user.is_superuser):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this student's schedule."
        )

    if db_student.school_class_id is None:
        # You could return an empty list or a specific message
        # For consistency, let's raise an error indicating they aren't in a class
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,  # Or 400 Bad Request
            detail="Student is not currently enrolled in any class, so no schedule is available."
        )

    # Fetch the student's class (ORM model) to get its grade for holiday checking
    # Ensure get_school_class_orm_by_id exists in crud_school_class
    db_student_class = crud.crud_school_class.get_school_class_orm_by_id(db, class_id=db_student.school_class_id)
    if not db_student_class:
        # This should be rare if school_class_id is valid and DB is consistent
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not retrieve class details for the student. Class may be missing."
        )

    # Fetch all weekly slots for the student's class (these are ORM models)
    # FastAPI's response_model will convert these to List[schemas.ClassScheduleSlot]
    weekly_slots_orm = crud.crud_schedule.get_schedule_slots_for_class(db=db,
                                                                       school_class_id=db_student.school_class_id)

    if target_date:
        # Check if the target_date is a holiday for this student's class's grade
        active_holidays = crud.crud_schedule.get_holidays_active_on_date(
            db=db, target_date=target_date, grade_filter_value=db_student_class.grade
        )
        if active_holidays:
            return []  # It's a holiday for this class on this specific date

        # Filter weekly slots for the target_date's day of the week
        target_day_of_week = target_date.weekday()  # Monday is 0, ..., Sunday is 6
        daily_schedule_slots = [
            slot for slot in weekly_slots_orm if slot.day_of_week == target_day_of_week
        ]
        return daily_schedule_slots
    else:
        # Return the full weekly schedule template for the student's class
        return weekly_slots_orm