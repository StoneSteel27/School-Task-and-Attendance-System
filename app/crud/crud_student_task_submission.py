
from sqlalchemy.orm import Session
from app import models, schemas
from app.models.task import StudentTaskSubmission
from datetime import datetime

def get_submissions_for_task(db: Session, *, task_id: int):
    return db.query(StudentTaskSubmission).filter(StudentTaskSubmission.task_id == task_id).all()

def get_submission(db: Session, *, submission_id: int):
    return db.query(StudentTaskSubmission).filter(StudentTaskSubmission.id == submission_id).first()

def create_submission(db: Session, *, submission_in: schemas.StudentTaskSubmissionCreate):
    db_obj = StudentTaskSubmission(**submission_in.model_dump())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def approve_submission(db: Session, *, db_obj: StudentTaskSubmission):
    db_obj.status = "APPROVED"
    db_obj.approved_at = datetime.utcnow()
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj
