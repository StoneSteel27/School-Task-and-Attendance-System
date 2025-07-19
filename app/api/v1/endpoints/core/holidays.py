from typing import List, Optional
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app import crud, models
from app.api import deps
from app.db.session import get_db
from app.schemas.core.school_class import SchoolClass as SchoolClassSchema, SchoolClassCreate, SchoolClassUpdate, BulkStudentRollNumbers, StudentAssignmentStatus, ClassTeacherAssignmentsCreate, ClassTeacherAssignmentsRemove, BatchAssignmentResult, ClassTeachingStaffDetail
from app.schemas.core.schedule import ClassScheduleSlot as ClassScheduleSlotSchema, Holiday as HolidaySchema, HolidayCreate, HolidayUpdate

router = APIRouter()


@router.get("/", response_model=List[HolidaySchema])
def read_holidays(
        db: Session = Depends(get_db),
        skip: int = 0,
        limit: int = 100,
        current_user: models.User = Depends(deps.get_current_active_user)
):
    """
    Retrieve holidays.
    """
    holidays = crud.crud_schedule.get_holidays(db, skip=skip, limit=limit)
    return holidays


@router.post("/", response_model=HolidaySchema)
def create_holiday(
        *,
        db: Session = Depends(get_db),
        holiday_in: HolidayCreate,
        current_user: models.User = Depends(deps.get_current_active_superuser)
):
    """
    Create new holiday.
    """
    holiday = crud.crud_schedule.create_holiday(db=db, holiday_in=holiday_in)
    return holiday


@router.put("/{holiday_id}", response_model=HolidaySchema)
def update_holiday(
        *,
        db: Session = Depends(get_db),
        holiday_id: int,
        holiday_in: HolidayUpdate,
        current_user: models.User = Depends(deps.get_current_active_superuser)
):
    """
    Update a holiday.
    """
    holiday = crud.crud_schedule.get_holiday_by_id(db=db, holiday_id=holiday_id)
    if not holiday:
        raise HTTPException(status_code=404, detail="Holiday not found")
    holiday = crud.crud_schedule.update_holiday(db=db, db_holiday=holiday, holiday_in=holiday_in)
    return holiday


@router.delete("/{holiday_id}", response_model=HolidaySchema)
def delete_holiday(
        *,
        db: Session = Depends(get_db),
        holiday_id: int,
        current_user: models.User = Depends(deps.get_current_active_superuser)
):
    """
    Delete a holiday.
    """
    holiday = crud.crud_schedule.get_holiday_by_id(db=db, holiday_id=holiday_id)
    if not holiday:
        raise HTTPException(status_code=404, detail="Holiday not found")
    holiday = crud.crud_schedule.delete_holiday(db=db, holiday_id=holiday_id)
    return holiday
