from typing import List, Optional
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app import crud, models
from app.api import deps
from app.db.session import get_db
from app.schemas.core.school_class import SchoolClass as SchoolClassSchema, SchoolClassCreate, SchoolClassUpdate, BulkStudentRollNumbers, StudentAssignmentStatus, ClassTeacherAssignmentsCreate, ClassTeacherAssignmentsRemove, BatchAssignmentResult, ClassTeachingStaffDetail
from app.schemas.core.schedule import ClassScheduleSlot as ClassScheduleSlotSchema

router = APIRouter()


@router.post("/", response_model=SchoolClassSchema, status_code=status.HTTP_201_CREATED)
def create_school_class(
        school_class: SchoolClassCreate,
        db: Session = Depends(get_db),
        current_user: models.User = Depends(deps.get_current_active_user)  # Any active user
):
    """
    Create a new school class with the given details.
    - Automatically assigns the class_code based on the next available code.
    - Initially, no students or teachers are assigned to the class.
    """
    # Check if a class with the same code already exists
    existing_class = crud.crud_school_class.get_school_class_by_class_code(db, class_code=school_class.class_code)
    if existing_class:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Class code already exists")

    # Create the school class
    new_class = crud.crud_school_class.create_school_class(db=db, school_class=school_class)
    return new_class


@router.get("/{class_code}", response_model=SchoolClassSchema)
def read_school_class(
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


@router.get("/", response_model=List[SchoolClassSchema])
def read_school_classes(
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


@router.put("/{class_code}", response_model=SchoolClassSchema)
def update_school_class(
        class_code: str,
        school_class_update: SchoolClassUpdate,
        db: Session = Depends(get_db),
        current_user: models.User = Depends(deps.get_current_active_user)  # Any active user
):
    """
    Update the details of an existing school class.
    Only the fields provided in the request will be updated.
    """
    db_class = crud.crud_school_class.get_school_class_by_class_code(db, class_code=class_code)
    if db_class is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="School class not found")

    updated_class = crud.crud_school_class.update_school_class(db=db, db_class=db_class, school_class_update=school_class_update)
    return updated_class


@router.delete("/{class_code}", response_model=SchoolClassSchema)
def delete_school_class(
        class_code: str,
        db: Session = Depends(get_db),
        current_user: models.User = Depends(deps.get_current_active_user)  # Any active user
):
    """
    Delete a school class by its class_code.
    This action will also unassign all students and teachers from the class.
    """
    db_class = crud.crud_school_class.get_school_class_by_class_code(db, class_code=class_code)
    if db_class is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="School class not found")

    # Delete the school class
    deleted_class = crud.crud_school_class.delete_school_class(db=db, db_class=db_class)
    return deleted_class


@router.get(
    "/{class_code}/teaching-staff",
    response_model=List[ClassTeachingStaffDetail]
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
    return [ClassTeachingStaffDetail(**staff) for staff in staff_details_dicts]


@router.get("/{class_code}/schedule", response_model=List[ClassScheduleSlotSchema], summary="Get Class Schedule")
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


@router.put("/{class_code}/schedule", response_model=List[ClassScheduleSlotSchema], summary="Replace Class Schedule")
def replace_class_schedule(
        class_code: str,
        schedule_slots: List[ClassScheduleSlotSchema],
        db: Session = Depends(get_db),
        current_user: models.User = Depends(deps.get_current_active_user)  # Any active user
):
    """
    Replace the entire schedule for a class on a specific date.
    - Deletes existing schedule slots for the date.
    - Adds new schedule slots from the request body.
    """
    db_class_orm = crud.crud_school_class.get_school_class_orm_by_class_code(db, class_code=class_code)
    if not db_class_orm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"School class with code '{class_code}' not found."
        )

    # Replace schedule logic
    updated_slots = crud.crud_schedule.replace_schedule_slots_for_class(
        db=db,
        school_class_id=db_class_orm.id,
        schedule_slots=schedule_slots
    )
    return updated_slots


@router.post("/{class_code}/students", response_model=List[StudentAssignmentStatus], summary="Assign Multiple Students to a Class")
def assign_students_to_class(
        class_code: str,
        student_roll_numbers: BulkStudentRollNumbers,
        db: Session = Depends(get_db),
        current_user: models.User = Depends(deps.get_current_active_user)  # Any active user
):
    """
    Assign multiple students to a class by their roll numbers.
    - Students will be added to the class if they are not already enrolled.
    - Returns the assignment status for each student.
    """
    db_class_orm = crud.crud_school_class.get_school_class_orm_by_class_code(db, class_code=class_code)
    if not db_class_orm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"School class with code '{class_code}' not found."
        )

    # Assign students to class
    assignment_results = crud.crud_student_assignment.assign_students_to_class(
        db=db,
        school_class=db_class_orm,
        roll_numbers=student_roll_numbers.roll_numbers
    )
    return assignment_results


@router.delete("/{class_code}/students", response_model=List[StudentAssignmentStatus], summary="Unassign Multiple Students from a Class")
def unassign_students_from_class(
        class_code: str,
        student_roll_numbers: BulkStudentRollNumbers,
        db: Session = Depends(get_db),
        current_user: models.User = Depends(deps.get_current_active_user)  # Any active user
):
    """
    Unassign multiple students from a class by their roll numbers.
    - Students will be removed from the class if they are currently enrolled.
    - Returns the unassignment status for each student.
    """
    db_class_orm = crud.crud_school_class.get_school_class_orm_by_class_code(db, class_code=class_code)
    if not db_class_orm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"School class with code '{class_code}' not found."
        )

    # Unassign students from class
    unassignment_results = crud.crud_student_assignment.unassign_students_from_class(
        db=db,
        school_class=db_class_orm,
        roll_numbers=student_roll_numbers.roll_numbers
    )
    return unassignment_results


@router.post("/{class_code}/teachers", response_model=List[BatchAssignmentResult], summary="Assign Multiple Teachers to Subjects in a Class")
def assign_teachers_to_class(
        class_code: str,
        teacher_assignments: List[ClassTeacherAssignmentsCreate],
        db: Session = Depends(get_db),
        current_user: models.User = Depends(deps.get_current_active_user)  # Any active user
):
    """
    Assign multiple teachers to subjects in a class.
    - Teachers will be assigned based on the provided subject and teacher IDs.
    - Returns the assignment result for each teacher-subject pair.
    """
    db_class_orm = crud.crud_school_class.get_school_class_orm_by_class_code(db, class_code=class_code)
    if not db_class_orm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"School class with code '{class_code}' not found."
        )

    # Assign teachers to class subjects
    assignment_results = crud.crud_teacher_assignment.assign_teachers_to_class(
        db=db,
        school_class=db_class_orm,
        teacher_assignments=teacher_assignments
    )
    return assignment_results


@router.delete("/{class_code}/teachers", response_model=List[BatchAssignmentResult], summary="Unassign Multiple Teachers from Subjects in a Class")
def unassign_teachers_from_class(
        class_code: str,
        teacher_assignments: List[ClassTeacherAssignmentsRemove],
        db: Session = Depends(get_db),
        current_user: models.User = Depends(deps.get_current_active_user)  # Any active user
):
    """
    Unassign multiple teachers from subjects in a class.
    - Teachers will be removed from the class's subjects based on the provided IDs.
    - Returns the unassignment result for each teacher-subject pair.
    """
    db_class_orm = crud.crud_school_class.get_school_class_orm_by_class_code(db, class_code=class_code)
    if not db_class_orm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"School class with code '{class_code}' not found."
        )

    # Unassign teachers from class subjects
    unassignment_results = crud.crud_teacher_assignment.unassign_teachers_from_class(
        db=db,
        school_class=db_class_orm,
        teacher_assignments=teacher_assignments
    )
    return unassignment_results
