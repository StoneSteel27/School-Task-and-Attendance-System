from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
# from sqlalchemy.exc import IntegrityError # Likely not needed for read-only operations

# Corrected imports
from app import crud, models, schemas
from app.db.session import get_db
from app.api import deps

router = APIRouter()

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
        current_user: models.User = Depends(deps.get_current_active_user) # Any active user
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
        current_user: models.User = Depends(deps.get_current_active_user) # Any active user
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
        current_user: models.User = Depends(deps.get_current_active_user) # Any active user
):
    """
    Get a specific holiday period by its ID.
    """
    db_holiday = crud.crud_schedule.get_holiday_by_id(db, holiday_id=holiday_id)
    if db_holiday is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Holiday not found")
    return db_holiday