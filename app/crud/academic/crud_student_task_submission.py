from sqlalchemy.orm import Session
from app import models, schemas
from app.models.academic.task import StudentTaskSubmission
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


# Create a simple object to provide access to all student task submission CRUD functions
class CRUDStudentTaskSubmission:
    """CRUD operations for StudentTaskSubmission model"""

    def get_submissions_for_task(self, db: Session, *, task_id: int):
        return get_submissions_for_task(db, task_id=task_id)

    def get(self, db: Session, *, submission_id: int):
        return get_submission(db, submission_id=submission_id)

    def create(self, db: Session, *, obj_in):
        return create_submission(db, submission_in=obj_in)

    def approve(self, db: Session, *, db_obj):
        return approve_submission(db, db_obj=db_obj)


# Create the instance that will be imported
student_task_submission = CRUDStudentTaskSubmission()
