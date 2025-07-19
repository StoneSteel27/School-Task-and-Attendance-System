import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import date, timedelta
import uuid

from app import crud, models, schemas
from app.core.config import settings
from app.core.security import get_password_hash
from app.models.academic.task import StudentTaskSubmission
from tests.conftest import get_auth_headers

# Fixture for a teacher user (can be reused from other test files if available)
@pytest.fixture(scope="function")
def test_teacher_user(db: Session) -> models.User:
    email = f"teacher_{uuid.uuid4().hex[:10]}@example.com"
    password = "testpassword"
    user_in = schemas.UserCreate(email=email, password=password, role="teacher", full_name="Test Teacher", roll_number=f"T{uuid.uuid4().hex[:5]}")
    user = crud.crud_user.create_user(db=db, user_in=user_in, password_hash=get_password_hash(password))
    return user

# Fixture for a student user
@pytest.fixture(scope="function")
def test_student_user(db: Session) -> models.User:
    email = f"student_{uuid.uuid4().hex[:10]}@example.com"
    password = "studentpassword"
    user_in = schemas.UserCreate(email=email, password=password, role="student", full_name="Test Student", roll_number=f"S{uuid.uuid4().hex[:5]}")
    user = crud.crud_user.create_user(db=db, user_in=user_in, password_hash=get_password_hash(password))
    return user

# Fixture for a school class
@pytest.fixture(scope="function")
def test_school_class(db: Session) -> models.SchoolClass:
    class_in = schemas.SchoolClassCreate(
        class_code=f"CLS-{uuid.uuid4().hex[:6]}",
        name="Test Class",
        grade="10",
        section="A"
    )
    school_class = crud.crud_school_class.create_school_class(db=db, class_in=class_in)
    return crud.crud_school_class.get_school_class_orm_by_id(db, class_id=school_class.id)

# Fixture for a task created by the teacher
@pytest.fixture(scope="function")
def test_task(db: Session, test_teacher_user: models.User, test_school_class: models.SchoolClass) -> models.Task:
    task_in = schemas.TaskCreate(
        title="Test Task",
        description="Test Description",
        due_date=date.today() + timedelta(days=5),
        subject="History"
    )
    task = crud.crud_task.create_task(
        db=db,
        task_in=task_in,
        school_class_id=test_school_class.id,
        created_by_teacher_id=test_teacher_user.id
    )
    return task

# Fixture for a submission by the student
@pytest.fixture(scope="function")
def test_submission(db: Session, test_task: models.Task, test_student_user: models.User) -> StudentTaskSubmission:
    submission_in = schemas.StudentTaskSubmissionCreate(
        task_id=test_task.id,
        student_id=test_student_user.id,
        submission_url="http://example.com/submission.pdf"
    )
    submission = crud.crud_student_task_submission.create_submission(db=db, submission_in=submission_in)
    return submission



# --- Tests for GET /tasks/{task_id}/submissions ---

def test_teacher_list_submissions_success(
    client: TestClient, db: Session, test_teacher_user: models.User, test_task: models.Task, test_submission: StudentTaskSubmission
):
    headers = get_auth_headers(client, test_teacher_user.email, "testpassword")
    response = client.get(f"{settings.API_V1_STR}/teachers/tasks/{test_task.id}/submissions", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == test_submission.id
    assert data[0]["student_id"] == test_submission.student_id

def test_teacher_list_submissions_unauthorized(
    client: TestClient, db: Session, test_task: models.Task, test_submission: StudentTaskSubmission
):
    # Create another teacher
    other_teacher = crud.crud_user.create_user(db, user_in=schemas.UserCreate(email="other@teacher.com", password="password", role="teacher", roll_number="T12345"), password_hash=get_password_hash("password"))
    headers = get_auth_headers(client, other_teacher.email, "password")
    response = client.get(f"{settings.API_V1_STR}/teachers/tasks/{test_task.id}/submissions", headers=headers)
    assert response.status_code == 403

def test_list_submissions_not_a_teacher(
    client: TestClient, db: Session, test_student_user: models.User, test_task: models.Task, test_submission: StudentTaskSubmission
):
    headers = get_auth_headers(client, test_student_user.email, "studentpassword")
    response = client.get(f"{settings.API_V1_STR}/teachers/tasks/{test_task.id}/submissions", headers=headers)
    assert response.status_code == 403


# --- Tests for PUT /submissions/{submission_id}/approve ---

def test_teacher_approve_submission_success(
    client: TestClient, db: Session, test_teacher_user: models.User, test_submission: StudentTaskSubmission
):
    headers = get_auth_headers(client, test_teacher_user.email, "testpassword")
    response = client.put(f"{settings.API_V1_STR}/teachers/submissions/{test_submission.id}/approve", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "APPROVED"
    assert data["approved_at"] is not None

    db.refresh(test_submission)
    assert test_submission.status == models.TaskStatus.APPROVED

def test_teacher_approve_submission_unauthorized(
    client: TestClient, db: Session, test_submission: StudentTaskSubmission
):
    other_teacher = crud.crud_user.create_user(db, user_in=schemas.UserCreate(email="other2@teacher.com", password="password", role="teacher", roll_number="T54321"), password_hash=get_password_hash("password"))
    headers = get_auth_headers(client, other_teacher.email, "password")
    response = client.put(f"{settings.API_V1_STR}/teachers/submissions/{test_submission.id}/approve", headers=headers)
    assert response.status_code == 403

def test_approve_submission_already_approved(
    client: TestClient, db: Session, test_teacher_user: models.User, test_submission: StudentTaskSubmission
):
    # First, approve the submission
    crud.crud_student_task_submission.approve_submission(db, db_obj=test_submission)

    headers = get_auth_headers(client, test_teacher_user.email, "testpassword")
    response = client.put(f"{settings.API_V1_STR}/teachers/submissions/{test_submission.id}/approve", headers=headers)
    assert response.status_code == 400

def test_approve_submission_not_a_teacher(
    client: TestClient, db: Session, test_student_user: models.User, test_submission: StudentTaskSubmission
):
    headers = get_auth_headers(client, test_student_user.email, "studentpassword")
    response = client.put(f"{settings.API_V1_STR}/teachers/submissions/{test_submission.id}/approve", headers=headers)
    assert response.status_code == 403
