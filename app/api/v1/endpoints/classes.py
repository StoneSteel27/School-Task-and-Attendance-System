from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
# sqlalchemy.exc.IntegrityError might not be needed here anymore if remaining endpoints don't cause it
# from sqlalchemy.exc import IntegrityError

# Corrected imports
from app import crud, models, schemas
from app.db.session import get_db
from app.api import deps

router = APIRouter()


@router.get("/", response_model=List[schemas.SchoolClass])
def read_school_classes_endpoint(
        db: Session = Depends(get_db),
        skip: int = 0,
        limit: int = 100,
        current_user: models.User = Depends(deps.get_current_active_user)  # Any active user
):
    """
    Retrieve all school classes, ordered by class_code.
    Includes student list and teaching staff for each class.
    """
    # crud.crud_school_class.get_school_classes already returns List[schemas.SchoolClass]
    # with students and teaching_staff populated.
    classes = crud.crud_school_class.get_school_classes(db, skip=skip, limit=limit)
    return classes


@router.get("/{class_code}", response_model=schemas.SchoolClass)
def read_school_class_by_code_endpoint(
        class_code: str,
        db: Session = Depends(get_db),
        current_user: models.User = Depends(deps.get_current_active_user)  # Any active user
):
    """
    Get a specific school class by its class_code, including enrolled students and teaching staff.
    """
    # crud.crud_school_class.get_school_class_by_class_code returns schemas.SchoolClass
    # with students and teaching_staff populated.
    db_class = crud.crud_school_class.get_school_class_by_class_code(db, class_code=class_code)
    if db_class is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="School class not found")
    return db_class


@router.get(
    "/{class_code}/teaching-staff",
    response_model=List[schemas.ClassTeachingStaffDetail]
)
def get_class_teaching_staff_endpoint(
        class_code: str,
        db: Session = Depends(get_db),
        current_user: models.User = Depends(deps.get_current_active_user)  # Any active user
):
    """
    Get the list of teachers and the subjects they teach for a specific class.
    """
    # get_school_class_orm_by_class_code is a helper to get the ORM model for CRUD operations
    db_class_orm = crud.crud_school_class.get_school_class_orm_by_class_code(db, class_code=class_code)
    if not db_class_orm:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="School class not found")

    staff_details_dicts = crud.crud_teacher_assignment.get_teaching_staff_for_class(db=db, school_class=db_class_orm)
    # Convert list of dicts to list of Pydantic models if necessary,
    # but schemas.ClassTeachingStaffDetail is what the CRUD returns in a list of dicts
    return [schemas.ClassTeachingStaffDetail(**staff) for staff in staff_details_dicts]


@router.get("/{class_code}/schedule", response_model=List[schemas.ClassScheduleSlot], summary="Get Class Schedule")
def get_class_schedule(
        class_code: str,
        target_date: Optional[date] = Query(None,
                                            description="If provided, returns the schedule for this specific date, considering holidays. Otherwise, returns the weekly template."),
        db: Session = Depends(get_db),
        current_user: models.User = Depends(deps.get_current_active_user)  # Any active user
):
    """
    Get the schedule for a specific school class.
    - If `target_date` is provided, it returns the schedule for that day,
      showing no slots if it's a holiday for the class's grade.
    - If `target_date` is omitted, it returns the full weekly schedule template.
    """
    db_class_orm = crud.crud_school_class.get_school_class_orm_by_class_code(db, class_code=class_code)
    if not db_class_orm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"School class with code '{class_code}' not found."
        )

    weekly_slots_orm = crud.crud_schedule.get_schedule_slots_for_class(db=db, school_class_id=db_class_orm.id)

    if target_date:
        active_holidays = crud.crud_schedule.get_holidays_active_on_date(
            db=db, target_date=target_date, grade_filter_value=db_class_orm.grade
        )
        if active_holidays:
            return []

        target_day_of_week = target_date.weekday()
        daily_schedule_slots = [
            slot for slot in weekly_slots_orm if slot.day_of_week == target_day_of_week
        ]
        return daily_schedule_slots  # FastAPI will convert ORM to Pydantic
    else:
        return weekly_slots_orm  # FastAPI will convert ORM to Pydantic
