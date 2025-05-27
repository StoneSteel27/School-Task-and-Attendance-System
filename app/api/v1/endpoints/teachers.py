from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
from datetime import date

from app import crud, models, schemas

from app.db.session import get_db
from app.api import deps

router = APIRouter()







@router.get(
    "/{teacher_roll_number}/teaching-load",
    response_model=List[schemas.TeacherTeachingDetail]
)
def get_teacher_teaching_load_endpoint(
    teacher_roll_number: str,
    db: Session = Depends(get_db),
    # Protected by: The teacher themselves or Superuser
    current_user: models.User = Depends(deps.get_current_active_user)
):
    """
    Get the list of classes and subjects a specific teacher is assigned to teach.
    Accessible by the teacher themselves or a superuser.
    """
    db_teacher = crud.crud_user.get_user_by_roll_number(db, roll_number=teacher_roll_number)
    if not db_teacher:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Teacher not found")

    # Authorization check
    if not current_user.is_superuser and current_user.id != db_teacher.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view this teacher's load.")

    assignments = crud.crud_teacher_assignment.get_assignments_for_teacher(db=db, teacher=db_teacher)
    return assignments


@router.get(
    "/{teacher_roll_number}/schedule",
    response_model=List[schemas.ClassScheduleSlot],  # Pydantic schema for response
    summary="Get Teacher's Schedule"
)
def get_teacher_schedule(
        teacher_roll_number: str,
        target_date: Optional[date] = Query(None,
                                            description="If provided, returns the schedule for this specific date. Otherwise, weekly template based on day_of_week or all."),
        day_of_week: Optional[int] = Query(None,
                                           description="Filter by specific day of the week (0=Monday, 6=Sunday). Used if target_date is not provided.",
                                           ge=0, le=6),
        db: Session = Depends(get_db),
        current_user: models.User = Depends(deps.get_current_active_user)
):
    """
    Get the schedule for a specific teacher.
    - If `target_date` is provided, it shows the schedule for that day,
      filtering out slots where the class has a holiday.
    - If only `day_of_week` is provided, it shows the teacher's schedule for that day from the weekly template.
    - If neither is provided, it returns the teacher's full weekly schedule template.
    - Access: Teacher themselves or a Superuser.
    """
    if target_date and day_of_week is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot specify both 'target_date' and 'day_of_week'. Use 'target_date' for a specific day's actual schedule or 'day_of_week' for a day in the weekly template."
        )

    db_teacher = crud.crud_user.get_user_by_roll_number(db, roll_number=teacher_roll_number)
    if not db_teacher:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Teacher not found")
    if db_teacher.role != "teacher":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"User with roll number {teacher_roll_number} is not a teacher.")

    # Authorization
    if not (current_user.id == db_teacher.id or current_user.is_superuser):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Not authorized to view this teacher's schedule.")

    slots_to_return_orm: List[models.ClassScheduleSlot] = []

    if target_date:
        day_of_week_from_date = target_date.weekday()
        # Get all slots for this teacher on this particular day of the week
        potential_slots_for_day_orm = crud.crud_schedule.get_schedule_slots_for_teacher(
            db, teacher_id=db_teacher.id, day_of_week=day_of_week_from_date
        )

        for slot_orm in potential_slots_for_day_orm:
            if not slot_orm.school_class:  # Should not happen if eager loading works and data is consistent
                # Log this issue, but might skip the slot or handle error
                continue

                # Check if the target_date is a holiday for the class associated with this slot
            active_holidays = crud.crud_schedule.get_holidays_active_on_date(
                db=db, target_date=target_date, grade_filter_value=slot_orm.school_class.grade
            )
            if not active_holidays:  # If it's NOT a holiday for this specific slot's class
                slots_to_return_orm.append(slot_orm)

    elif day_of_week is not None:
        # Get slots for a specific day of the weekly template
        slots_to_return_orm = crud.crud_schedule.get_schedule_slots_for_teacher(
            db, teacher_id=db_teacher.id, day_of_week=day_of_week
        )
    else:
        slots_to_return_orm = crud.crud_schedule.get_schedule_slots_for_teacher(db, teacher_id=db_teacher.id)

    # FastAPI's response_model will convert List[models.ClassScheduleSlot] to List[schemas.ClassScheduleSlot]
    return slots_to_return_orm