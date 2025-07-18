
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app import crud, models, schemas
from app.api import deps

router = APIRouter()

@router.get(
    "/tasks/{task_id}/submissions",
    response_model=List[schemas.StudentTaskSubmission],
    summary="Teacher: List submissions for a task"
)
def list_task_submissions(
    task_id: int,
    db: Session = Depends(deps.get_db),
    current_teacher: models.User = Depends(deps.get_current_active_user),
):
    """
    Allows a teacher to see all submissions for a specific task they created.
    """
    if current_teacher.role != "teacher":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only teachers can view submissions.")

    task = crud.crud_task.get_task(db, task_id=task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found.")

    if task.created_by_teacher_id != current_teacher.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not authorized to view submissions for this task.")

    submissions = crud.crud_student_task_submission.get_submissions_for_task(db, task_id=task_id)
    return submissions

@router.put(
    "/submissions/{submission_id}/approve",
    response_model=schemas.StudentTaskSubmission,
    summary="Teacher: Approve a submission"
)
def approve_submission(
    submission_id: int,
    db: Session = Depends(deps.get_db),
    current_teacher: models.User = Depends(deps.get_current_active_user),
):
    """
    Allows a teacher to approve a student's submission.
    """
    if current_teacher.role != "teacher":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only teachers can approve submissions.")

    submission = crud.crud_student_task_submission.get_submission(db, submission_id=submission_id)
    if not submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found.")

    task = crud.crud_task.get_task(db, task_id=submission.task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Associated task not found.")

    if task.created_by_teacher_id != current_teacher.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not authorized to approve submissions for this task.")

    if submission.status == "APPROVED":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Submission is already approved.")

    approved_submission = crud.crud_student_task_submission.approve_submission(db, db_obj=submission)
    return approved_submission
