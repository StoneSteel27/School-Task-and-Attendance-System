from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from sqlalchemy.exc import IntegrityError

# Corrected imports to use absolute paths from 'app'
from app import crud, models, schemas
from app.db.session import get_db
from app.api import deps # This should resolve to app/api/deps.py

router = APIRouter()

@router.post("/", response_model=schemas.SchoolClass, status_code=status.HTTP_201_CREATED)
def create_school_class_endpoint(
        *,
        db: Session = Depends(get_db),
        class_in: schemas.SchoolClassCreate,
        current_user: models.User = Depends(deps.get_current_active_superuser)
):
    """
    Create a new school class using class_code as the primary business identifier.
    Admin access required.
    """
    try:
        created_class = crud.crud_school_class.create_school_class(db=db, class_in=class_in)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A school class with the class code '{class_in.class_code}' already exists.",
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while creating the class: {str(e)}",
        )
    return created_class

@router.put("/{class_code}", response_model=schemas.SchoolClass)
def update_school_class_endpoint(
        class_code: str,
        *,
        db: Session = Depends(get_db),
        class_in: schemas.SchoolClassUpdate,
        current_user: models.User = Depends(deps.get_current_active_superuser)
):
    """
    Update a school class identified by class_code.
    Admin access required.
    """
    db_class_orm = crud.crud_school_class.get_school_class_orm_by_class_code(db, class_code=class_code)
    if not db_class_orm:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="School class not found")

    try:
        updated_class_schema = crud.crud_school_class.update_school_class(
            db=db, db_class=db_class_orm, class_in=class_in
        )
    except IntegrityError:
        db.rollback()
        detail_msg = "Failed to update school class."
        if class_in.class_code: # Check if class_code was part of the update payload
            existing_class_check = crud.crud_school_class.get_school_class_orm_by_class_code(db, class_code=class_in.class_code)
            if existing_class_check and existing_class_check.id != db_class_orm.id:
                 detail_msg = f"Failed to update. Another class with class code '{class_in.class_code}' already exists."
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail_msg,
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while updating the class: {str(e)}",
        )
    return updated_class_schema

@router.delete("/{class_code}", response_model=schemas.SchoolClass)
def delete_school_class_endpoint(
        class_code: str,
        db: Session = Depends(get_db),
        current_user: models.User = Depends(deps.get_current_active_superuser)
):
    """
    Delete a school class identified by class_code.
    Returns the details of the class as it was before deletion.
    Admin access required.
    """
    db_class_orm_to_delete = crud.crud_school_class.get_school_class_orm_by_class_code(db, class_code=class_code)
    if not db_class_orm_to_delete:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="School class not found")

    deleted_class_schema = crud.crud_school_class.remove_school_class(db=db, db_class_to_delete=db_class_orm_to_delete)
    return deleted_class_schema

@router.post(
    "/{class_code}/students/class-assign",
    response_model=List[schemas.StudentAssignmentStatus],
    status_code=status.HTTP_207_MULTI_STATUS
)
def bulk_assign_students_to_class_endpoint(
        class_code: str,
        payload: schemas.BulkStudentRollNumbers,
        db: Session = Depends(get_db),
        current_admin_user: models.User = Depends(deps.get_current_active_superuser)
):
    """
    Bulk assign multiple students (by roll number) to this school class.
    Returns a status for each student roll number provided.
    Admin access required.
    """
    # get_school_class_by_class_code returns a Pydantic model, we need ORM model for CRUD
    db_class = crud.crud_school_class.get_school_class_orm_by_class_code(db, class_code=class_code)
    if not db_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"School class with code '{class_code}' not found."
        )

    assignment_results = crud.crud_user.bulk_assign_students_to_class(
        db=db,
        student_roll_numbers=payload.student_roll_numbers,
        target_school_class=db_class
    )
    return assignment_results

@router.post(
    "/{class_code}/students/class-unassign",
    response_model=List[schemas.StudentAssignmentStatus],
    status_code=status.HTTP_207_MULTI_STATUS
)
def bulk_unassign_students_from_class_endpoint(
        class_code: str,
        payload: schemas.BulkStudentRollNumbers,
        db: Session = Depends(get_db),
        current_admin_user: models.User = Depends(deps.get_current_active_superuser)
):
    """
    Bulk unassign multiple students (by roll number) from this school class.
    Returns a status for each student roll number provided.
    Admin access required.
    """
    # get_school_class_by_class_code returns a Pydantic model, we need ORM model for CRUD
    db_class = crud.crud_school_class.get_school_class_orm_by_class_code(db, class_code=class_code)
    if not db_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"School class with code '{class_code}' not found."
        )

    unassignment_results = crud.crud_user.bulk_unassign_students_from_class(
        db=db,
        student_roll_numbers=payload.student_roll_numbers,
        source_school_class=db_class
    )
    return unassignment_results

@router.post(
    "/{class_code}/assign-teachers",
    response_model=List[schemas.BatchAssignmentResult],
    status_code=status.HTTP_207_MULTI_STATUS
)
def batch_assign_teachers_to_class_endpoint(
        class_code: str,
        payload: schemas.ClassTeacherAssignmentsCreate,
        db: Session = Depends(get_db),
        current_admin_user: models.User = Depends(deps.get_current_active_superuser)
):
    """
    Batch assign multiple teachers to various subjects for a specific school class.
    Admin access required.
    """
    # get_school_class_by_class_code returns a Pydantic model, we need ORM model for CRUD
    db_class = crud.crud_school_class.get_school_class_orm_by_class_code(db, class_code=class_code)
    if not db_class:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"School class with code '{class_code}' not found.")

    results: List[schemas.BatchAssignmentResult] = []
    for assignment_detail in payload.assignments:
        teacher_roll_number = assignment_detail.teacher_roll_number
        subject = assignment_detail.subject
        current_op_result = schemas.BatchAssignmentResult(
            teacher_roll_number=teacher_roll_number, subject=subject, status="processing", detail=""
        )
        db_teacher = crud.crud_user.get_user_by_roll_number(db, roll_number=teacher_roll_number)
        if not db_teacher:
            current_op_result.status = "error_teacher_not_found"
            current_op_result.detail = f"Teacher with roll number '{teacher_roll_number}' not found."
            results.append(current_op_result)
            continue
        if db_teacher.role != "teacher":
            current_op_result.status = "error_not_a_teacher"
            current_op_result.detail = f"User '{teacher_roll_number}' is not a teacher."
            results.append(current_op_result)
            continue
        is_already_assigned = crud.crud_teacher_assignment.check_teacher_assigned_to_class_subject(
            db=db, teacher=db_teacher, school_class=db_class, subject=subject
        )
        if is_already_assigned:
            current_op_result.status = "already_exists"
            current_op_result.detail = "Teacher already assigned this subject in this class."
        else:
            try:
                crud.crud_teacher_assignment.assign_teacher_to_class_subject(
                    db=db, teacher=db_teacher, school_class=db_class, subject=subject
                )
                current_op_result.status = "assigned"
                current_op_result.detail = "Successfully assigned."
            except ValueError as ve:
                db.rollback()
                current_op_result.status = "error_validation"
                current_op_result.detail = str(ve)
            except Exception as e:
                db.rollback()
                current_op_result.status = "error_unknown_assignment"
                current_op_result.detail = f"Failed to assign: {str(e)}"
        results.append(current_op_result)
    return results

@router.post(
    "/{class_code}/unassign-teachers",
    response_model=List[schemas.BatchAssignmentResult],
    status_code=status.HTTP_207_MULTI_STATUS
)
def batch_unassign_teachers_from_class_endpoint(
        class_code: str,
        payload: schemas.ClassTeacherAssignmentsRemove,
        db: Session = Depends(get_db),
        current_admin_user: models.User = Depends(deps.get_current_active_superuser)
):
    """
    Batch unassign multiple teachers from various subjects for a specific school class.
    Admin access required.
    """
    # get_school_class_by_class_code returns a Pydantic model, we need ORM model for CRUD
    db_class = crud.crud_school_class.get_school_class_orm_by_class_code(db, class_code=class_code)
    if not db_class:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"School class with code '{class_code}' not found.")

    results: List[schemas.BatchAssignmentResult] = []
    for assignment_detail in payload.assignments:
        teacher_roll_number = assignment_detail.teacher_roll_number
        subject = assignment_detail.subject
        current_op_result = schemas.BatchAssignmentResult(
            teacher_roll_number=teacher_roll_number, subject=subject, status="processing", detail=""
        )
        db_teacher = crud.crud_user.get_user_by_roll_number(db, roll_number=teacher_roll_number)
        if not db_teacher:
            current_op_result.status = "error_teacher_not_found"
            current_op_result.detail = f"Teacher with roll number '{teacher_roll_number}' not found."
            results.append(current_op_result)
            continue
        is_assigned = crud.crud_teacher_assignment.check_teacher_assigned_to_class_subject(
            db=db, teacher=db_teacher, school_class=db_class, subject=subject
        )
        if not is_assigned:
            current_op_result.status = "not_found"
            current_op_result.detail = "Teacher was not assigned this subject in this class."
        else:
            try:
                deleted = crud.crud_teacher_assignment.unassign_teacher_from_class_subject(
                    db=db, teacher=db_teacher, school_class=db_class, subject=subject
                )
                if deleted:
                    current_op_result.status = "removed"
                    current_op_result.detail = "Successfully unassigned."
                else:
                    current_op_result.status = "error_not_removed"
                    current_op_result.detail = "Assignment existed but failed to unassign."
            except Exception as e:
                db.rollback()
                current_op_result.status = "error_unknown_unassignment"
                current_op_result.detail = f"Failed to unassign: {str(e)}"
        results.append(current_op_result)
    return results

@router.post(
    "/{class_code}/schedule",
    response_model=List[schemas.ClassScheduleSlot],
    status_code=status.HTTP_201_CREATED,
    summary="Set or Replace Class Weekly Schedule (Admin)"
)
def set_or_replace_class_schedule_admin( # Renamed to avoid conflict if classes.py had a similar public one
        class_code: str,
        payload: schemas.ClassScheduleSlotsBulkCreate,
        db: Session = Depends(get_db),
        current_superuser: models.User = Depends(deps.get_current_active_superuser)
):
    """
    Set or replace the entire weekly schedule for a specific class.
    Admin access required.
    """
    db_class = crud.crud_school_class.get_school_class_orm_by_class_code(db, class_code=class_code)
    if not db_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"School class with code '{class_code}' not found."
        )
    try:
        created_slots_orm = crud.crud_schedule.replace_schedule_for_class(
            db=db, school_class_id=db_class.id, new_slots_data=payload.slots
        )
        return created_slots_orm
    except IntegrityError as e:
        db.rollback()
        detail = "Failed to set schedule due to a conflict (e.g., teacher double booking, or invalid data)."
        if hasattr(e, 'orig') and e.orig: # Check if e.orig exists before accessing
            detail = f"Failed to set schedule. Conflict detected: {e.orig}"
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )