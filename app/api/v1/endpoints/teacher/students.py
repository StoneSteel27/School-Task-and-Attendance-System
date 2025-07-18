from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app import crud, models, schemas
from app.api import deps

router = APIRouter()


@router.get("/search", response_model=List[schemas.User])
def search_students(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_teacher),
    name: Optional[str] = Query(None, description="Search by student name (first or last, partial match)"),
    roll_number: Optional[str] = Query(None, description="Search by student roll number (exact match)"),
    class_code: Optional[str] = Query(None, description="Search by class code (exact match)"),
):
    """
    Search for students. Teachers can only search for students in their classes.
    """
    if not any([name, roll_number, class_code]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one search parameter (name, roll_number, or class_code) must be provided.",
        )

    # Get the classes the teacher is assigned to
    teacher_assignments = crud.crud_teacher_assignment.get_assignments_for_teacher(db, teacher=current_user)
    teacher_class_ids = {assignment['school_class_id'] for assignment in teacher_assignments}

    if not teacher_class_ids:
        return []

    students = crud.crud_user.search_students_for_teacher(
        db,
        teacher_class_ids=list(teacher_class_ids),
        name=name,
        roll_number=roll_number,
        class_code=class_code,
    )
    return students
