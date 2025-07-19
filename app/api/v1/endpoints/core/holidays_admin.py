from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

# Corrected imports to use absolute paths from 'app'
from app import crud, models, schemas
from app.db.session import get_db
from app.api import deps # This should resolve to app/api/deps.py

router = APIRouter()

@router.post(
    "/",
    response_model=schemas.Holiday,
    status_code=status.HTTP_201_CREATED
)
def create_new_holiday(
        *,
        db: Session = Depends(get_db),
        holiday_in: schemas.HolidayCreate,
        current_superuser: models.User = Depends(deps.get_current_active_superuser) # Added dependency
):
    """
    Create a new holiday period. Superuser access required.
    """
    try:
        holiday = crud.crud_schedule.create_holiday(db=db, holiday_in=holiday_in)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create holiday. Possible database integrity issue.",
        )
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(ve))
    return holiday

@router.post(
    "/bulk-create",
    response_model=List[schemas.Holiday],
    status_code=status.HTTP_201_CREATED
)
def create_bulk_holidays(
        *,
        db: Session = Depends(get_db),
        holidays_payload: schemas.HolidayBulkCreate,
        current_superuser: models.User = Depends(deps.get_current_active_superuser) # Added dependency
):
    """
    Create multiple holiday periods in bulk. Superuser access required.
    If any holiday in the batch fails, the entire operation is rolled back.
    """
    try:
        created_holidays = crud.crud_schedule.bulk_create_holidays(db=db, holidays_in=holidays_payload.holidays)
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(ve))
    return created_holidays

@router.put(
    "/{holiday_id}",
    response_model=schemas.Holiday
)
def update_existing_holiday(
        holiday_id: int,
        *,
        db: Session = Depends(get_db),
        holiday_in: schemas.HolidayUpdate,
        current_superuser: models.User = Depends(deps.get_current_active_superuser) # Added dependency
):
    """
    Update an existing holiday period. Superuser access required.
    """
    db_holiday = crud.crud_schedule.get_holiday_by_id(db, holiday_id=holiday_id)
    if not db_holiday:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Holiday not found")

    temp_start_date = holiday_in.start_date if holiday_in.start_date is not None else db_holiday.start_date
    temp_end_date = holiday_in.end_date if holiday_in.end_date is not None else db_holiday.end_date
    if temp_end_date < temp_start_date:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Update results in end_date being before start_date."
        )

    try:
        updated_holiday = crud.crud_schedule.update_holiday(db=db, db_holiday=db_holiday, holiday_in=holiday_in)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update holiday. Possible database integrity issue.",
        )
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(ve))
    return updated_holiday

@router.delete(
    "/{holiday_id}",
    response_model=schemas.Holiday
)
def delete_existing_holiday(
        holiday_id: int,
        db: Session = Depends(get_db),
        current_superuser: models.User = Depends(deps.get_current_active_superuser) # Added dependency
):
    """
    Delete a holiday period by its ID. Superuser access required.
    """
    deleted_holiday = crud.crud_schedule.delete_holiday(db=db, holiday_id=holiday_id)
    if not deleted_holiday:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Holiday not found")
    return deleted_holiday