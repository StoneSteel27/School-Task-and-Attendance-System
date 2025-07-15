# app/api/v1/endpoints/teacher/homeroom_attendance.py
from fastapi import APIRouter, Depends, HTTPException, status, Path
from sqlalchemy.orm import Session
from typing import List
from datetime import date

from app import crud, models, schemas  # Using __all__ from app's __init__ or direct imports
from app.api import deps  # For get_current_active_user etc.
from app.db.session import get_db
from app.models.student_attendance import AttendanceSession  # Direct import for clarity

router = APIRouter()


@router.post(
    "/{class_code}/submit",  # Path relative to the prefix in teacher/__init__.py
    response_model=schemas.ClassAttendanceSubmissionResponse,
    status_code=status.HTTP_201_CREATED
    # Consider HTTP_207_MULTI_STATUS if you want to explicitly indicate partial success/failure
)
def submit_homeroom_class_attendance(
        class_code: str,
        submission_payload: schemas.ClassAttendanceSubmission,  # Contains date, session, and student entries
        db: Session = Depends(get_db),
        current_user: models.User = Depends(deps.get_current_active_user)
):
    """
    Submit attendance for all students in a specific homeroom class for a given date and session.
    The authenticated user must be a teacher and the homeroom teacher for the specified class.
    """
    # 1. Verify user is a teacher
    if current_user.role != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only users with the 'teacher' role can perform this action."
        )

    # 2. Fetch the target class using its class_code
    # get_school_class_orm_by_class_code returns the ORM model or None
    db_class = crud.crud_school_class.get_school_class_orm_by_class_code(db, class_code=class_code)
    if not db_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"School class with code '{class_code}' not found."
        )

    # 3. Verify current teacher is the homeroom teacher for this class
    if db_class.homeroom_teacher_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"You are not the designated homeroom teacher for class '{class_code}'."
        )

    # 4. Call CRUD function to create/process attendance records
    # The CRUD function handles individual student validations (exists, in class, not already recorded)
    crud_results_list_of_dicts = crud.crud_student_attendance.create_class_attendance_records(
        db=db,
        entries=submission_payload.entries,
        attendance_date=submission_payload.attendance_date,
        session=submission_payload.session,
        school_class_id=db_class.id,
        teacher_id=current_user.id
    )

    # 5. Process CRUD results to build the API response object
    response_items: List[schemas.ClassAttendanceSubmissionResultItem] = []
    successful_creation_count = 0
    failed_creation_count = 0

    for res_dict in crud_results_list_of_dicts:
        # The res_dict from CRUD already contains student_roll_number and student_full_name
        item = schemas.ClassAttendanceSubmissionResultItem(**res_dict)
        response_items.append(item)
        if item.outcome == "SUCCESS":  # Assuming CRUD uses "SUCCESS" for successful creation
            successful_creation_count += 1
        else:
            failed_creation_count += 1

    # Determine overall status and potentially HTTP status code based on outcomes
    # For simplicity, we'll stick with 201 if the request itself was valid and processed.
    # The response body will detail individual successes/failures.

    return schemas.ClassAttendanceSubmissionResponse(
        school_class_id=db_class.id,
        school_class_code=db_class.class_code,
        attendance_date=submission_payload.attendance_date,
        session=submission_payload.session,
        marked_by_teacher_id=current_user.id,
        marked_by_teacher_name=current_user.full_name,  # Assuming User model has full_name
        total_students_in_payload=len(submission_payload.entries),
        successful_records=successful_creation_count,
        failed_records=failed_creation_count,
        results=response_items
    )


@router.get(
    "/{class_code}/{attendance_date_str}/{session_str}",
    response_model=List[schemas.StudentAttendanceRecord]
)
def get_homeroom_class_attendance_by_date_session(
        class_code: str = Path(..., description="The class code of the homeroom class."),
        attendance_date_str: str = Path(..., description="Date in YYYY-MM-DD format."),
        session_str: str = Path(..., description="Session: MORNING or AFTERNOON (case-insensitive)."),
        db: Session = Depends(get_db),
        current_user: models.User = Depends(deps.get_current_active_user)
):
    """
    Get all attendance records for a specific homeroom class, date, and session.
    The authenticated user must be the homeroom teacher for the specified class.
    """
    # 1. Verify user is a teacher
    if current_user.role != "teacher":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only teachers can access this.")

    # 2. Validate date and session string inputs
    try:
        attendance_date = date.fromisoformat(attendance_date_str)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid date format. Use YYYY-MM-DD.")

    try:
        # Convert to uppercase for case-insensitive matching with enum values
        session = AttendanceSession(session_str.upper())
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Invalid session. Use MORNING or AFTERNOON.")

    # 3. Fetch the target class
    db_class = crud.crud_school_class.get_school_class_orm_by_class_code(db, class_code=class_code)
    if not db_class:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"School class with code '{class_code}' not found.")

    # 4. Verify current teacher is the homeroom teacher for this class
    if db_class.homeroom_teacher_id != current_user.id:
        # Also allow superusers to view any class attendance through this teacher-specific route if desired,
        # or keep it strictly for the homeroom teacher. For now, strict to homeroom.
        # if not current_user.is_superuser: # <-- Uncomment to allow superusers
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail=f"You are not the homeroom teacher for class '{class_code}'.")

    # 5. Fetch attendance records using the CRUD function
    attendance_orm_list = crud.crud_student_attendance.get_attendance_for_class_on_date_session(
        db=db, school_class_id=db_class.id, attendance_date=attendance_date, session=session
    )

    # The response_model=List[schemas.StudentAttendanceRecord] will handle the conversion
    # of ORM objects to Pydantic schemas, including the nested StudentInfo, SchoolClassInfo, TeacherInfo.
    return attendance_orm_list