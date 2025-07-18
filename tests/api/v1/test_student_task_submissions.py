
import os
import uuid
from datetime import date, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.core.config import settings
from app.core.security import get_password_hash

# Use a separate directory for test submissions to avoid cluttering the main one
TEST_SUBMISSIONS_DIR = Path("test_submissions")


@pytest.fixture(scope="session", autouse=True)
def setup_test_submissions_dir():
    """Create the test submissions directory before tests run and clean up after."""
    TEST_SUBMISSIONS_DIR.mkdir(exist_ok=True)
    yield
    # Cleanup: remove all files from the directory after tests are done
    for item in TEST_SUBMISSIONS_DIR.iterdir():
        item.unlink()
    TEST_SUBMISSIONS_DIR.rmdir()


@pytest.fixture(scope="function")
def test_school_class(db: Session) -> models.SchoolClass:
    """Fixture to create a school class for tests."""
    class_code = f"TEST-CLASS-{uuid.uuid4().hex[:6]}"
    class_in = schemas.SchoolClassCreate(
        class_code=class_code, name="Test Class", grade="10", section="A"
    )
    school_class = crud.crud_school_class.create_school_class(db=db, class_in=class_in)
    db.commit()
    db.refresh(school_class)
    return school_class


@pytest.fixture(scope="function")
def test_student(db: Session, test_school_class: models.SchoolClass) -> models.User:
    """Fixture to create a student user enrolled in the test_school_class."""
    student_in = schemas.UserCreate(
        email=f"student_{uuid.uuid4().hex[:6]}@test.com",
        password="testpassword",
        full_name="Test Student",
        roll_number=f"STUDENT-{uuid.uuid4().hex[:6]}",
        role="student",
    )
    hashed_password = get_password_hash("testpassword")
    student = crud.crud_user.create_user(
        db=db, user_in=student_in, password_hash=hashed_password
    )
    student.school_class_id = test_school_class.id
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


@pytest.fixture(scope="function")
def student_auth_headers(
    client: TestClient, test_student: models.User
) -> dict[str, str]:
    """Fixture to get authentication headers for the test_student."""
    login_data = {"username": test_student.email, "password": "testpassword"}
    r = client.post(f"{settings.API_V1_STR}/auth/login/access-token", data=login_data)
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def test_teacher(db: Session) -> models.User:
    """Fixture to create a teacher user."""
    teacher_in = schemas.UserCreate(
        email=f"teacher_{uuid.uuid4().hex[:6]}@test.com",
        password="testpassword",
        full_name="Test Teacher",
        roll_number=f"TEACHER-{uuid.uuid4().hex[:6]}",
        role="teacher",
    )
    hashed_password = get_password_hash("testpassword")
    return crud.crud_user.create_user(
        db=db, user_in=teacher_in, password_hash=hashed_password
    )


@pytest.fixture(scope="function")
def test_task(
    db: Session, test_teacher: models.User, test_school_class: models.SchoolClass
) -> models.Task:
    """Fixture to create a task assigned to the test_school_class by the test_teacher."""
    # Assign teacher to the class/subject to allow task creation
    crud.crud_teacher_assignment.assign_teacher_to_class_subject(
        db, teacher=test_teacher, school_class=test_school_class, subject="Science"
    )
    task_in = schemas.TaskCreate(
        title="Test Task",
        description="This is a test task.",
        due_date=date.today() + timedelta(days=5),
        subject="Science",
    )
    return crud.crud_task.create_task(
        db,
        task_in=task_in,
        school_class_id=test_school_class.id,
        created_by_teacher_id=test_teacher.id,
    )


def test_student_submit_task_successfully(
    client: TestClient,
    db: Session,
    test_student: models.User,
    student_auth_headers: dict[str, str],
    test_task: models.Task,
):
    """
    GIVEN a student and a task assigned to their class
    WHEN the student submits a file for the task
    THEN the submission should be successful (200 OK)
    AND the file should be saved
    AND the database should record the submission
    """
    # Arrange
    print(f"Student's class ID: {test_student.school_class_id}")
    print(f"Task's class ID: {test_task.school_class_id}")
    file_content = b"This is the content of my submission."
    file_name = "my_submission.txt"
    url = f"{settings.API_V1_STR}/students/me/tasks/{test_task.id}/submit"

    # Act
    with open(os.path.join(TEST_SUBMISSIONS_DIR, file_name), "wb") as f:
        f.write(file_content)

    with open(os.path.join(TEST_SUBMISSIONS_DIR, file_name), "rb") as f:
        response = client.post(
            url, headers=student_auth_headers, files={"file": (file_name, f, "text/plain")}
        )

    # Assert
    assert response.status_code == 200
    submission_data = response.json()

    assert submission_data["task_id"] == test_task.id
    assert submission_data["student_id"] == test_student.id
    assert submission_data["status"] == "SUBMITTED"
    assert submission_data["submission_url"] is not None

    # Verify file was saved correctly
    saved_file_path = Path(submission_data["submission_url"])
    assert saved_file_path.exists()
    assert saved_file_path.read_bytes() == file_content

    # Verify DB record
    db_submission = crud.crud_task.get_student_task_submission(
        db, task_id=test_task.id, student_id=test_student.id
    )
    assert db_submission is not None
    assert Path(db_submission.submission_url) == saved_file_path

    # Cleanup
    saved_file_path.unlink()


def test_student_submit_task_for_non_existent_task(
    client: TestClient, test_student: models.User, student_auth_headers: dict[str, str]
):
    """
    GIVEN a student
    WHEN the student submits a file for a task that does not exist
    THEN the submission should fail with a 404 Not Found error
    """
    # Arrange
    non_existent_task_id = 9999
    url = f"{settings.API_V1_STR}/students/me/tasks/{non_existent_task_id}/submit"
    file_content = b"some content"
    file_name = "test.txt"

    # Act
    with open(os.path.join(TEST_SUBMISSIONS_DIR, file_name), "wb") as f:
        f.write(file_content)
    with open(os.path.join(TEST_SUBMISSIONS_DIR, file_name), "rb") as f:
        response = client.post(
            url, headers=student_auth_headers, files={"file": (file_name, f, "text/plain")}
        )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found."


def test_student_submit_task_for_other_class(
    client: TestClient,
    db: Session,
    test_student: models.User,
    student_auth_headers: dict[str, str],
    test_teacher: models.User,
):
    """
    GIVEN a student and a task assigned to a different class
    WHEN the student attempts to submit a file for that task
    THEN the submission should fail with a 403 Forbidden error
    """
    # Arrange: Create a different class and a task for it
    other_class_in = schemas.SchoolClassCreate(
        class_code=f"OTHER-CLASS-{uuid.uuid4().hex[:6]}",
        name="Other Class",
        grade="11",
        section="B",
    )
    other_class = crud.crud_school_class.create_school_class(db, class_in=other_class_in)
    crud.crud_teacher_assignment.assign_teacher_to_class_subject(
        db, teacher=test_teacher, school_class=other_class, subject="History"
    )
    other_task_in = schemas.TaskCreate(
        title="Other Task",
        description="A task for another class.",
        due_date=date.today() + timedelta(days=3),
        subject="History",
    )
    other_task = crud.crud_task.create_task(
        db,
        task_in=other_task_in,
        school_class_id=other_class.id,
        created_by_teacher_id=test_teacher.id,
    )

    url = f"{settings.API_V1_STR}/students/me/tasks/{other_task.id}/submit"
    file_content = b"some content"
    file_name = "test.txt"

    # Act
    with open(os.path.join(TEST_SUBMISSIONS_DIR, file_name), "wb") as f:
        f.write(file_content)
    with open(os.path.join(TEST_SUBMISSIONS_DIR, file_name), "rb") as f:
        response = client.post(
            url, headers=student_auth_headers, files={"file": (file_name, f, "text/plain")}
        )

    # Assert
    assert response.status_code == 403
    assert response.json()["detail"] == "Task is not assigned to this student's class."


def test_unauthorized_user_cannot_submit_task(
    client: TestClient, test_student: models.User, test_task: models.Task
):
    """
    GIVEN a student and a task
    WHEN a request is made to submit a file without authentication
    THEN the request should fail with a 401 Unauthorized error
    """
    # Arrange
    url = f"{settings.API_V1_STR}/students/me/tasks/{test_task.id}/submit"
    file_content = b"some content"
    file_name = "test.txt"

    # Act
    with open(os.path.join(TEST_SUBMISSIONS_DIR, file_name), "wb") as f:
        f.write(file_content)
    with open(os.path.join(TEST_SUBMISSIONS_DIR, file_name), "rb") as f:
        response = client.post(url, files={"file": (file_name, f, "text/plain")})

    # Assert
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

