from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from app import crud, models, schemas  # Import from relevant __init__.py
from app.db.session import get_db
from app.api import deps
from sqlalchemy.exc import IntegrityError

router = APIRouter()


@router.post("/", response_model=schemas.SchoolClass, status_code=status.HTTP_201_CREATED)
def create_school_class_endpoint(
        *,
        db: Session = Depends(get_db),
        class_in: schemas.SchoolClassCreate,  # class_in now requires class_code
        current_user: models.User = Depends(deps.get_current_active_superuser)
):
    """
    Create a new school class using class_code as the primary business identifier.
    """
    try:
        created_class = crud.crud_school_class.create_school_class(db=db, class_in=class_in)
    except IntegrityError:  # Specifically catch IntegrityError (e.g., for unique constraint)
        db.rollback()  # Rollback the session
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A school class with the class code '{class_in.class_code}' already exists.",
        )
    except Exception as e:  # Catch other potential errors during creation
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while creating the class: {str(e)}",
        )
    return created_class


@router.get("/", response_model=List[schemas.SchoolClass])
def read_school_classes_endpoint(
        db: Session = Depends(get_db),
        skip: int = 0,
        limit: int = 100,
        current_user: models.User = Depends(deps.get_current_active_user)
):
    """
    Retrieve all school classes, ordered by class_code.
    """
    classes = crud.crud_school_class.get_school_classes(db, skip=skip, limit=limit)
    return classes


@router.get("/{class_code}", response_model=schemas.SchoolClass)
def read_school_class_by_code_endpoint(  # Renamed function for clarity
        class_code: str,  # Path parameter is now class_code (string)
        db: Session = Depends(get_db),
        current_user: models.User = Depends(deps.get_current_active_user)
):
    """
    Get a specific school class by its class_code, including enrolled students.
    """
    db_class = crud.crud_school_class.get_school_class_by_class_code(db, class_code=class_code)
    if db_class is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="School class not found")
    return db_class


@router.put("/{class_code}", response_model=schemas.SchoolClass)
def update_school_class_endpoint(
        class_code: str,  # Path parameter
        *,
        db: Session = Depends(get_db),
        class_in: schemas.SchoolClassUpdate,
        current_user: models.User = Depends(deps.get_current_active_superuser)
):
    """
    Update a school class identified by class_code.
    """
    # Fetch the ORM model instance of the class to be updated
    db_class_orm = crud.crud_school_class.get_school_class_orm_by_class_code(db, class_code=class_code)
    if not db_class_orm:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="School class not found")

    # The crud_school_class.update_school_class function expects the ORM model
    # and will return the updated class as a Pydantic schema.
    try:
        updated_class_schema = crud.crud_school_class.update_school_class(
            db=db, db_class=db_class_orm, class_in=class_in
        )
    except IntegrityError:  # Catch potential IntegrityError if new class_code is not unique
        db.rollback()
        # class_in.class_code might be None if not being updated.
        # If it's part of class_in and being changed, it's relevant.
        detail_msg = "Failed to update school class."
        if class_in.class_code:
            detail_msg = f"Failed to update. Another class with class code '{class_in.class_code}' might already exist."
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
        class_code: str,  # Path parameter
        db: Session = Depends(get_db),
        current_user: models.User = Depends(deps.get_current_active_superuser)
):
    """
    Delete a school class identified by class_code.
    Returns the details of the class as it was before deletion.
    """
    # Fetch the ORM model instance of the class to be deleted
    db_class_orm_to_delete = crud.crud_school_class.get_school_class_orm_by_class_code(db, class_code=class_code)
    if not db_class_orm_to_delete:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="School class not found")

    # The crud_school_class.remove_school_class function expects the ORM model
    # and will return the deleted class as a Pydantic schema.
    deleted_class_schema = crud.crud_school_class.remove_school_class(db=db, db_class_to_delete=db_class_orm_to_delete)
    return deleted_class_schema


@router.post(
    "/{class_code}/students/class-assign",
    response_model=List[schemas.StudentAssignmentStatus],
    status_code=status.HTTP_207_MULTI_STATUS
)
def bulk_assign_students_to_class_endpoint(
        class_code: str,
        payload: schemas.BulkStudentRollNumbers,  # New schema for request body
        db: Session = Depends(get_db),
        current_admin_user: models.User = Depends(deps.get_current_active_superuser)
):
    """
    Bulk assign multiple students (by roll number) to this school class.
    Returns a status for each student roll number provided.
    """
    db_class = crud.crud_school_class.get_school_class_by_class_code(db, class_code=class_code)
    if not db_class:
        # If the class itself doesn't exist, we can't assign anyone.
        # A 404 for the class is appropriate.
        # Alternatively, could return a 207 with all student statuses as "error_class_not_found"
        # For simplicity, let's make class existence a prerequisite.
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"School class with code '{class_code}' not found."
        )

    # Call the new bulk CRUD function
    assignment_results = crud.crud_user.bulk_assign_students_to_class(
        db=db,
        student_roll_numbers=payload.student_roll_numbers,
        target_school_class=db_class
    )
    return assignment_results


@router.post(  # Using POST because it has a request body.
    "/{class_code}/students/class-unassign",
    response_model=List[schemas.StudentAssignmentStatus],
    status_code=status.HTTP_207_MULTI_STATUS
)
def bulk_unassign_students_from_class_endpoint(
        class_code: str,
        payload: schemas.BulkStudentRollNumbers,  # Reusing the same schema for the list of roll numbers
        db: Session = Depends(get_db),
        current_admin_user: models.User = Depends(deps.get_current_active_superuser)
):
    """
    Bulk unassign multiple students (by roll number) from this school class.
    Returns a status for each student roll number provided.
    """
    db_class = crud.crud_school_class.get_school_class_by_class_code(db, class_code=class_code)
    if not db_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"School class with code '{class_code}' not found."
        )

    # Call the new bulk CRUD function
    unassignment_results = crud.crud_user.bulk_unassign_students_from_class(
        db=db,
        student_roll_numbers=payload.student_roll_numbers,
        source_school_class=db_class  # Pass the class they are being unassigned from
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
    Accessible only by superusers.
    """
    db_class = crud.crud_school_class.get_school_class_by_class_code(db, class_code=class_code)
    if not db_class:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"School class with code '{class_code}' not found.")

    results: List[schemas.BatchAssignmentResult] = []

    for assignment_detail in payload.assignments:
        teacher_roll_number = assignment_detail.teacher_roll_number
        subject = assignment_detail.subject

        # Initialize result entry for this specific assignment
        current_op_result = schemas.BatchAssignmentResult(
            teacher_roll_number=teacher_roll_number,
            subject=subject,
            status="processing",  # Default status
            detail=""
        )

        db_teacher = crud.crud_user.get_user_by_roll_number(db, roll_number=teacher_roll_number)
        if not db_teacher:
            current_op_result.status = "error_teacher_not_found"
            current_op_result.detail = f"Teacher with roll number '{teacher_roll_number}' not found."
            results.append(current_op_result)
            continue  # Move to next assignment in batch

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
                )  # This CRUD function now commits on its own
                current_op_result.status = "assigned"
                current_op_result.detail = "Successfully assigned."
            except ValueError as ve:  # Should be caught by role check above, but as safeguard
                db.rollback()  # Ensure rollback if CRUD tried to commit
                current_op_result.status = "error_validation"
                current_op_result.detail = str(ve)
            except Exception as e:  # Catch unexpected errors during the assignment
                db.rollback()
                current_op_result.status = "error_unknown_assignment"
                current_op_result.detail = f"Failed to assign: {str(e)}"

        results.append(current_op_result)

        return results


@router.post(  # Using POST for body, could also be DELETE if your client/framework supports DELETE with body easily
    "/{class_code}/unassign-teachers",
    response_model=List[schemas.BatchAssignmentResult],
    status_code=status.HTTP_207_MULTI_STATUS
)
def batch_unassign_teachers_from_class_endpoint(
        class_code: str,
        payload: schemas.ClassTeacherAssignmentsRemove,  # Contains list of {teacher_roll_number, subject}
        db: Session = Depends(get_db),
        current_admin_user: models.User = Depends(deps.get_current_active_superuser)
):
    """
    Batch unassign multiple teachers from various subjects for a specific school class.
    Accessible only by superusers.
    """
    db_class = crud.crud_school_class.get_school_class_by_class_code(db, class_code=class_code)
    if not db_class:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"School class with code '{class_code}' not found.")

    results: List[schemas.BatchAssignmentResult] = []

    for assignment_detail in payload.assignments:
        teacher_roll_number = assignment_detail.teacher_roll_number
        subject = assignment_detail.subject

        current_op_result = schemas.BatchAssignmentResult(
            teacher_roll_number=teacher_roll_number,
            subject=subject,
            status="processing",
            detail=""
        )

        db_teacher = crud.crud_user.get_user_by_roll_number(db, roll_number=teacher_roll_number)
        if not db_teacher:
            current_op_result.status = "error_teacher_not_found"
            current_op_result.detail = f"Teacher with roll number '{teacher_roll_number}' not found."
            results.append(current_op_result)
            continue

        # Role check isn't strictly necessary for unassignment if we assume only teachers could have been assigned.

        is_assigned = crud.crud_teacher_assignment.check_teacher_assigned_to_class_subject(
            db=db, teacher=db_teacher, school_class=db_class, subject=subject
        )
        if not is_assigned:
            current_op_result.status = "not_found"  # Assignment to remove does not exist
            current_op_result.detail = "Teacher was not assigned this subject in this class."
        else:
            try:
                # crud_teacher_assignment.unassign_teacher_from_class_subject returns True if deleted
                deleted = crud.crud_teacher_assignment.unassign_teacher_from_class_subject(
                    db=db, teacher=db_teacher, school_class=db_class, subject=subject
                )  # This CRUD function commits on its own
                if deleted:
                    current_op_result.status = "removed"
                    current_op_result.detail = "Successfully unassigned."
                else:
                    # This case should ideally be caught by 'is_assigned' check above
                    # but as a safeguard if CRUD logic changes
                    current_op_result.status = "error_not_removed"
                    current_op_result.detail = "Assignment existed but failed to unassign."
            except Exception as e:
                db.rollback()
                current_op_result.status = "error_unknown_unassignment"
                current_op_result.detail = f"Failed to unassign: {str(e)}"

        results.append(current_op_result)
    return results


@router.get(
    "/{class_code}/teaching-staff",
    response_model=List[schemas.ClassTeachingStaffDetail]
)
def get_class_teaching_staff_endpoint(
        class_code: str,
        db: Session = Depends(get_db),
        current_user: models.User = Depends(deps.get_current_active_user)  # Any active user can see this
):
    """
    Get the list of teachers and the subjects they teach for a specific class.
    """
    db_class = crud.crud_school_class.get_school_class_by_class_code(db, class_code=class_code)
    if not db_class:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="School class not found")

    staff_details = crud.crud_teacher_assignment.get_teaching_staff_for_class(db=db, school_class=db_class)
    return staff_details


@router.post(
    "/{class_code}/schedule",
    response_model=List[schemas.ClassScheduleSlot],  # Pydantic schema for response
    status_code=status.HTTP_201_CREATED,
    summary="Set or Replace Class Weekly Schedule"
)
def set_or_replace_class_schedule(
        class_code: str,
        payload: schemas.ClassScheduleSlotsBulkCreate,  # Pydantic schema for request body
        db: Session = Depends(get_db),
        current_superuser: models.User = Depends(deps.get_current_active_superuser)
):
    """
    Set or replace the entire weekly schedule for a specific class.
    This operation is idempotent for a given payload; it deletes existing slots
    for the class and creates new ones based on the payload.
    - Requires superuser privileges.
    """
    db_class = crud.crud_school_class.get_school_class_orm_by_class_code(db, class_code=class_code)
    if not db_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"School class with code '{class_code}' not found."
        )

    try:
        # crud_schedule.replace_schedule_for_class returns List[models.ClassScheduleSlot]
        # FastAPI's response_model will convert these ORM objects to List[schemas.ClassScheduleSlot]
        created_slots_orm = crud.crud_schedule.replace_schedule_for_class(
            db=db, school_class_id=db_class.id, new_slots_data=payload.slots
        )
        return created_slots_orm
    except IntegrityError as e:
        db.rollback()  # Ensure rollback from this layer too
        # e.orig often contains the specific database error message
        detail = "Failed to set schedule due to a conflict (e.g., teacher double booking, or invalid data)."
        if hasattr(e, 'orig') and e.orig:
            detail = f"Failed to set schedule. Conflict detected: {e.orig}"
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )
    except Exception as e:  # Catch any other unexpected errors
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@router.get("/{class_code}/schedule", response_model=List[schemas.ClassScheduleSlot], summary="Get Class Schedule")
def get_class_schedule(
        class_code: str,
        target_date: Optional[date] = Query(None,
                                            description="If provided, returns the schedule for this specific date, considering holidays. Otherwise, returns the weekly template."),
        db: Session = Depends(get_db),
        current_user: models.User = Depends(deps.get_current_active_user)  # Any active user can view
):
    """
    Get the schedule for a specific school class.
    - If `target_date` is provided, it returns the schedule for that day,
      showing no slots if it's a holiday for the class's grade.
    - If `target_date` is omitted, it returns the full weekly schedule template.
    """
    # We need the ORM model of the class to access its grade for holiday checking.
    db_class = crud.crud_school_class.get_school_class_orm_by_class_code(db, class_code=class_code)
    if not db_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"School class with code '{class_code}' not found."
        )

    # Fetch all weekly slots (these are ORM models)
    # This list will be converted to List[schemas.ClassScheduleSlot] by FastAPI's response_model
    weekly_slots_orm = crud.crud_schedule.get_schedule_slots_for_class(db=db, school_class_id=db_class.id)

    if target_date:
        # Check if the target_date is a holiday for this class's grade
        active_holidays = crud.crud_schedule.get_holidays_active_on_date(
            db=db, target_date=target_date, grade_filter_value=db_class.grade
            # Assuming SchoolClass model has a 'grade' attribute
        )
        if active_holidays:
            return []  # It's a holiday for this class on this specific date

        target_day_of_week = target_date.weekday()  # Monday is 0, ..., Sunday is 6
        daily_schedule_slots = [
            slot for slot in weekly_slots_orm if slot.day_of_week == target_day_of_week
        ]
        return daily_schedule_slots
    else:
        # Return the full weekly schedule template
        return weekly_slots_orm
