from fastapi import APIRouter, Depends, HTTPException, status, Path, Query
from sqlalchemy.orm import Session
from typing import List
from datetime import date

from app import crud, models, schemas
from app.api import deps
from app.db.session import get_db
from app.models.attendance.student_attendance import AttendanceSession
from app.schemas.attendance.student_attendance import ClassAttendancePercentageSummary, StudentAttendanceRecord

router = APIRouter()

@router.get(
    "/student/{student_roll_number}",
    response_model=List[StudentAttendanceRecord],
    summary="Admin: Get Student Attendance Records by Roll Number"
)
def admin_read_student_attendance_records(
    student_roll_number: str = Path(..., description="The roll number of the student whose records are to be retrieved."),
    start_date_str: str = Query(..., alias="startDate", description="Start date for the attendance records search range (YYYY-MM-DD)."),
    end_date_str: str = Query(..., alias="endDate", description="End date for the attendance records search range (YYYY-MM-DD)."),
    skip: int = Query(0, ge=0, description="Number of records to skip for pagination."),
    limit: int = Query(100, ge=1, le=200, description="Maximum number of records to return."),
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(deps.get_current_active_superuser)
):
    """
    Retrieve attendance records for a specific student over a given date range.
    Accessible only by superusers.
    """
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

    target_student_user = crud.crud_user.get_user_by_roll_number(db, roll_number=student_roll_number)
    if not target_student_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with roll number '{student_roll_number}' not found."
        )
    if target_student_user.role != "student":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User with roll number '{student_roll_number}' is a {target_student_user.role}, not a student."
        )

    attendance_records = crud.crud_student_attendance.get_attendance_for_student_date_range(
        db=db,
        student_id=target_student_user.id,
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=limit
    )
    return attendance_records

@router.get(
    "/class/{class_code}/{attendance_date_str}/{session_str}",
    response_model=List[StudentAttendanceRecord],
    summary="Admin: Get Classroom Attendance by Date and Session"
)
def admin_read_classroom_attendance(
    class_code: str = Path(..., description="The class code of the classroom."),
    attendance_date_str: str = Path(..., description="Date of attendance in YYYY-MM-DD format."),
    session_str: str = Path(..., description="Attendance session: MORNING or AFTERNOON (case-insensitive)."),
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(deps.get_current_active_superuser)
):
    """
    Retrieve all attendance records for a specific classroom, date, and session.
    Accessible only by superusers.
    """
    try:
        attendance_date = date.fromisoformat(attendance_date_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format. Use YYYY-MM-DD."
        )

    try:
        session = AttendanceSession(session_str.upper())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid session. Use MORNING or AFTERNOON."
        )

    target_class_orm = crud.crud_school_class.get_school_class_orm_by_class_code(db, class_code=class_code)
    if not target_class_orm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"School class with code '{class_code}' not found."
        )

    attendance_records = crud.crud_student_attendance.get_attendance_for_class_on_date_session(
        db=db,
        school_class_id=target_class_orm.id,
        attendance_date=attendance_date,
        session=session
    )
    return attendance_records

@router.get(
    "/class/{class_code}/{attendance_date_str}/{session_str}/summary",
    response_model=ClassAttendancePercentageSummary, # Use the new schema
    summary="Admin: Get Classroom Attendance Percentage Summary",
    tags=["Admin - Student Attendance"] # Ensure it's grouped with other admin attendance routes
)
def admin_read_classroom_attendance_summary(
    class_code: str = Path(..., description="The class code of the classroom for which to generate the summary."),
    attendance_date_str: str = Path(..., description="Date for the attendance summary in YYYY-MM-DD format."),
    session_str: str = Path(..., description="Attendance session for the summary: MORNING or AFTERNOON (case-insensitive)."),
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(deps.get_current_active_superuser)
):
    """
    Retrieve a summary of attendance percentages and counts for a specific classroom,
    date, and session. Accessible only by superusers.
    """
    try:
        attendance_date = date.fromisoformat(attendance_date_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format. Use YYYY-MM-DD."
        )

    try:
        # Convert to uppercase for case-insensitive matching with enum values
        session_enum_value = AttendanceSession(session_str.upper())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid session. Use MORNING or AFTERNOON."
        )

    # Fetch the class ORM model to get its ID and verify existence
    db_school_class = crud.crud_school_class.get_school_class_orm_by_class_code(db, class_code=class_code)
    if not db_school_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"School class with code '{class_code}' not found."
        )

    # Call the CRUD function to get the summary data
    summary_data_dict = crud.crud_student_attendance.get_class_attendance_summary(
        db=db,
        school_class_id=db_school_class.id,
        attendance_date=attendance_date,
        session=session_enum_value
    )

    if summary_data_dict is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, # Or 404 if class was deleted between checks
            detail=f"Could not generate attendance summary for class '{class_code}'. The class may have been deleted or an internal error occurred."
        )

    return summary_data_dict