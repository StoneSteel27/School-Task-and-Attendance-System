from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.db.session import get_db
from app import models, schemas, crud
from app.schemas.attendance import AttendanceRequest
from app.schemas.attendance import TeacherAttendanceBase, TeacherAttendanceCreate

router = APIRouter()

@router.post("/check-in", response_model=schemas.TeacherAttendanceInDB)
def check_in(
    *,
    db: Session = Depends(get_db),
    attendance_data: AttendanceRequest,
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """
    Check in the current teacher, verifying their location and creating an attendance record.
    """
    if current_user.role != "teacher":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only teachers can check in.")

    location_check = deps.geofence_manager.check_location_against_geofences(
        current_lat=attendance_data.latitude,
        current_lon=attendance_data.longitude,
        geofences=deps.SCHOOL_GEOFENCES
    )

    if not location_check["is_within_geofence"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are not within the school premises."
        )

    last_check_in = crud.teacher_attendance.get_last_check_in(db, teacher_id=current_user.id)
    if last_check_in:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already checked in. Please check out first."
        )
    
    attendance_record = crud.teacher_attendance.create_check_in(db, teacher=current_user)
    return attendance_record

@router.post("/check-out", response_model=schemas.TeacherAttendanceInDB)
def check_out(
    *,
    db: Session = Depends(get_db),
    attendance_data: AttendanceRequest,
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """
    Check out the current teacher, verifying their location and updating the attendance record.
    """
    if current_user.role != "teacher":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only teachers can check out.")

    location_check = deps.geofence_manager.check_location_against_geofences(
        current_lat=attendance_data.latitude,
        current_lon=attendance_data.longitude,
        geofences=deps.SCHOOL_GEOFENCES
    )

    if not location_check["is_within_geofence"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are not within the school premises."
        )

    last_check_in = crud.teacher_attendance.get_last_check_in(db, teacher_id=current_user.id)
    if not last_check_in:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have not checked in yet."
        )
        
    attendance_record = crud.teacher_attendance.update_check_out(db, db_obj=last_check_in)
    return attendance_record
