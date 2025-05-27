from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app import crud, models, schemas
from app.api import deps
from app.db.session import get_db

router = APIRouter()


@router.post(
    "/",
    response_model=schemas.Holiday,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(deps.get_current_active_superuser)]
)
def create_new_holiday(
        *,
        db: Session = Depends(get_db),
        holiday_in: schemas.HolidayCreate,
):
    """
    Create a new holiday period. Superuser access required.
    """
    try:
        holiday = crud.crud_schedule.create_holiday(db=db, holiday_in=holiday_in)
    except IntegrityError:  # Should be rare now with ranges, but for other DB constraints
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create holiday. Possible database integrity issue (e.g. invalid foreign key if any, or other constraint).",
        )
    except ValueError as ve:  # From Pydantic validation if not caught earlier or other value errors
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(ve))
    return holiday


@router.post(
    "/bulk-create",
    response_model=List[schemas.Holiday],
    status_code=status.HTTP_201_CREATED,  # Simplistic: 201 if batch attempted, errors could still occur
    dependencies=[Depends(deps.get_current_active_superuser)]
)
def create_bulk_holidays(
        *,
        db: Session = Depends(get_db),
        holidays_payload: schemas.HolidayBulkCreate,
):
    """
    Create multiple holiday periods in bulk. Superuser access required.
    If any holiday in the batch fails (e.g., due to a database error), the entire operation is rolled back.
    """
    try:
        created_holidays = crud.crud_schedule.bulk_create_holidays(db=db, holidays_in=holidays_payload.holidays)
    except IntegrityError as e:
        db.rollback()
        # The CRUD function now raises a more specific IntegrityError message
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)  # Pass the detailed error message from CRUD
        )
    except ValueError as ve:  # From Pydantic validation if not caught earlier
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(ve))
    return created_holidays


@router.get("/", response_model=List[schemas.Holiday])
def read_holidays(
        db: Session = Depends(get_db),
        skip: int = 0,
        limit: int = 100,
        query_start_date: Optional[date] = Query(None,
                                                 description="Find holidays overlapping or starting after this date"),
        query_end_date: Optional[date] = Query(None,
                                               description="Find holidays overlapping or ending before this date"),
        grade_filter_value: Optional[str] = Query(None,
                                                  description="Filter holidays for a specific grade (e.g., '5') or all (if omitted/null in DB)"),
        current_user: models.User = Depends(deps.get_current_active_user)  # Any active user can view holidays
):
    """
    Retrieve a list of holiday periods.
    Can be filtered by a date range (finds overlapping holidays) and by applicable grade.
    """
    holidays = crud.crud_schedule.get_holidays(
        db,
        skip=skip,
        limit=limit,
        query_start_date=query_start_date,
        query_end_date=query_end_date,
        grade_filter_value=grade_filter_value
    )
    return holidays


@router.get("/check-date", response_model=List[schemas.Holiday])
def check_if_date_is_holiday(
        target_date: date = Query(..., description="The specific date to check for holidays."),
        grade_filter_value: Optional[str] = Query(None,
                                                  description="Grade to check against (e.g., '5'). If omitted, checks for school-wide holidays or matches any grade-specific holiday for the date."),
        db: Session = Depends(get_db),
        current_user: models.User = Depends(deps.get_current_active_user)
):
    """
    Check if a specific date falls within any holiday period, optionally for a specific grade.
    Returns a list of holiday periods active on that date. Empty if not a holiday.
    """
    active_holidays = crud.crud_schedule.get_holidays_active_on_date(
        db=db, target_date=target_date, grade_filter_value=grade_filter_value
    )
    return active_holidays


@router.get("/{holiday_id}", response_model=schemas.Holiday)
def read_holiday_by_id(
        holiday_id: int,
        db: Session = Depends(get_db),
        current_user: models.User = Depends(deps.get_current_active_user)
):
    """
    Get a specific holiday period by its ID.
    """
    db_holiday = crud.crud_schedule.get_holiday_by_id(db, holiday_id=holiday_id)
    if db_holiday is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Holiday not found")
    return db_holiday


@router.put(
    "/{holiday_id}",
    response_model=schemas.Holiday,
    dependencies=[Depends(deps.get_current_active_superuser)]
)
def update_existing_holiday(
        holiday_id: int,
        *,
        db: Session = Depends(get_db),
        holiday_in: schemas.HolidayUpdate,
):
    """
    Update an existing holiday period. Superuser access required.
    """
    db_holiday = crud.crud_schedule.get_holiday_by_id(db, holiday_id=holiday_id)
    if not db_holiday:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Holiday not found")

    # Add server-side validation for date order if only one date is updated
    # This complements the Pydantic validator which only runs if both dates are in holiday_in
    temp_start_date = holiday_in.start_date if holiday_in.start_date is not None else db_holiday.start_date
    temp_end_date = holiday_in.end_date if holiday_in.end_date is not None else db_holiday.end_date
    if temp_end_date < temp_start_date:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Update results in end_date being before start_date."
        )

    try:
        updated_holiday = crud.crud_schedule.update_holiday(db=db, db_holiday=db_holiday, holiday_in=holiday_in)
    except IntegrityError:  # Should be rare now, but for other DB constraints
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update holiday. Possible database integrity issue.",
        )
    except ValueError as ve:  # From Pydantic or other value errors
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(ve))
    return updated_holiday


@router.delete(
    "/{holiday_id}",
    response_model=schemas.Holiday,
    dependencies=[Depends(deps.get_current_active_superuser)]
)
def delete_existing_holiday(
        holiday_id: int,
        db: Session = Depends(get_db),
):
    """
    Delete a holiday period by its ID. Superuser access required.
    """
    deleted_holiday = crud.crud_schedule.delete_holiday(db=db, holiday_id=holiday_id)
    if not deleted_holiday:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Holiday not found")
    return deleted_holiday