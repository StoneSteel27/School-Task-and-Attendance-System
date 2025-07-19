import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import date, timedelta
import uuid

from app import crud, models, schemas
from app.core.config import settings
from app.core.security import get_password_hash
from tests.conftest import test_teacher_direct_fixture, test_teacher_user, get_auth_headers


# Helper fixture to create a school class
@pytest.fixture(scope="function")
def test_school_class(db: Session) -> models.SchoolClass:
    class_in = schemas.SchoolClassCreate(
        class_code=f"GR10-B-{uuid.uuid4().hex[:6]}",
        name="Grade 10 Section B",
        grade="10",
        section="B"
    )
    school_class_schema = crud.crud_school_class.create_school_class(db=db, class_in=class_in)
    school_class_orm = crud.crud_school_class.get_school_class_orm_by_class_code(db, class_code=school_class_schema.class_code)
    return school_class_orm

# Helper fixture to assign teacher to a class and subject
@pytest.fixture(scope="function")
def assigned_teacher_to_class_subject(db: Session, test_teacher_user: models.User, test_school_class: models.SchoolClass):
    crud.crud_teacher_assignment.assign_teacher_to_class_subject(
        db=db, teacher=test_teacher_user, school_class=test_school_class, subject="Mathematics"
    )
    db.refresh(test_teacher_user)
    db.refresh(test_school_class)
    return test_teacher_user, test_school_class, "Mathematics"


# --- Task Endpoints Tests ---

def test_teacher_create_task_success(client: TestClient, test_teacher_direct_fixture: dict, assigned_teacher_to_class_subject):
    teacher, school_class, subject = assigned_teacher_to_class_subject
    task_data = {
        "title": "Algebra Homework",
        "description": "Complete exercises 1-10 from Chapter 3.",
        "due_date": (date.today() + timedelta(days=7)).isoformat(),
        "subject": subject
    }
    response = client.post(
        f"{settings.API_V1_STR}/teachers/classes/{school_class.class_code}/tasks",
        json=task_data,
        headers=test_teacher_direct_fixture
    )
    assert response.status_code == 201
    content = response.json()
    assert content["title"] == task_data["title"]
    assert content["school_class_id"] == school_class.id
    assert content["created_by_teacher_id"] == teacher.id


def test_teacher_create_task_unauthorized_role(client: TestClient, normal_user_token_headers: dict, test_school_class: models.SchoolClass):
    task_data = {
        "title": "Algebra Homework",
        "description": "Complete exercises 1-10 from Chapter 3.",
        "due_date": (date.today() + timedelta(days=7)).isoformat(),
        "subject": "Mathematics"
    }
    response = client.post(
        f"{settings.API_V1_STR}/teachers/classes/{test_school_class.class_code}/tasks",
        json=task_data,
        headers=normal_user_token_headers
    )
    assert response.status_code == 403


def test_teacher_create_task_class_not_found(client: TestClient, test_teacher_direct_fixture: dict):
    task_data = {
        "title": "Algebra Homework",
        "description": "Complete exercises 1-10 from Chapter 3.",
        "due_date": (date.today() + timedelta(days=7)).isoformat(),
        "subject": "Mathematics"
    }
    response = client.post(
        f"{settings.API_V1_STR}/teachers/classes/NONEXISTENT-CLASS/tasks",
        json=task_data,
        headers=test_teacher_direct_fixture
    )
    assert response.status_code == 404


def test_teacher_create_task_not_assigned_to_subject(client: TestClient, test_teacher_direct_fixture: dict, test_school_class: models.SchoolClass):
    # Teacher is not assigned to any subject in this class
    task_data = {
        "title": "Algebra Homework",
        "description": "Complete exercises 1-10 from Chapter 3.",
        "due_date": (date.today() + timedelta(days=7)).isoformat(),
        "subject": "Physics" # Teacher is not assigned to Physics
    }
    response = client.post(
        f"{settings.API_V1_STR}/teachers/classes/{test_school_class.class_code}/tasks",
        json=task_data,
        headers=test_teacher_direct_fixture
    )
    assert response.status_code == 403


def test_teacher_get_tasks_for_class_success(client: TestClient, test_teacher_direct_fixture: dict, assigned_teacher_to_class_subject, db: Session):
    teacher, school_class, subject = assigned_teacher_to_class_subject
    # Create a task first
    task_data = schemas.TaskCreate(
        title="Math Test Prep",
        description="Review chapters 1-5.",
        due_date=date.today() + timedelta(days=10),
        subject=subject
    )
    crud.crud_task.create_task(db=db, task_in=task_data, school_class_id=school_class.id, created_by_teacher_id=teacher.id)

    response = client.get(
        f"{settings.API_V1_STR}/teachers/classes/{school_class.class_code}/tasks",
        headers=test_teacher_direct_fixture
    )
    assert response.status_code == 200
    content = response.json()
    assert len(content) >= 1
    assert any(task["title"] == "Math Test Prep" for task in content)


def test_teacher_get_tasks_for_class_filter_by_subject(client: TestClient, test_teacher_direct_fixture: dict, assigned_teacher_to_class_subject, db: Session):
    teacher, school_class, math_subject = assigned_teacher_to_class_subject
    # Create a Math task
    math_task_data = schemas.TaskCreate(
        title="Math Homework",
        description="Do math problems.",
        due_date=date.today() + timedelta(days=5),
        subject=math_subject
    )
    crud.crud_task.create_task(db=db, task_in=math_task_data, school_class_id=school_class.id, created_by_teacher_id=teacher.id)

    # Assign teacher to another subject and create a task for it
    other_subject = "Physics"
    crud.crud_teacher_assignment.assign_teacher_to_class_subject(
        db=db, teacher=teacher, school_class=school_class, subject=other_subject
    )
    physics_task_data = schemas.TaskCreate(
        title="Physics Lab Report",
        description="Write lab report.",
        due_date=date.today() + timedelta(days=10),
        subject=other_subject
    )
    crud.crud_task.create_task(db=db, task_in=physics_task_data, school_class_id=school_class.id, created_by_teacher_id=teacher.id)

    # Get tasks filtered by Math
    response = client.get(
        f"{settings.API_V1_STR}/teachers/classes/{school_class.class_code}/tasks?subject={math_subject}",
        headers=test_teacher_direct_fixture
    )
    assert response.status_code == 200
    content = response.json()
    assert len(content) == 1
    assert content[0]["title"] == "Math Homework"
    assert content[0]["subject"] == math_subject


def test_teacher_update_task_success(client: TestClient, test_teacher_direct_fixture: dict, assigned_teacher_to_class_subject, db: Session):
    teacher, school_class, subject = assigned_teacher_to_class_subject
    task_data = schemas.TaskCreate(
        title="Original Task",
        description="Original Description",
        due_date=date.today() + timedelta(days=7),
        subject=subject
    )
    created_task = crud.crud_task.create_task(db=db, task_in=task_data, school_class_id=school_class.id, created_by_teacher_id=teacher.id)

    update_data = {"title": "Updated Task Title", "description": "New Description"}
    response = client.put(
        f"{settings.API_V1_STR}/teachers/tasks/{created_task.id}",
        json=update_data,
        headers=test_teacher_direct_fixture
    )
    assert response.status_code == 200
    content = response.json()
    assert content["title"] == update_data["title"]
    assert content["description"] == update_data["description"]


def test_teacher_update_task_unauthorized_teacher(client: TestClient, assigned_teacher_to_class_subject, db: Session):
    teacher, school_class, subject = assigned_teacher_to_class_subject
    task = crud.crud_task.create_task(
        db=db,
        task_in=schemas.TaskCreate(title="Another Task", description="Desc", due_date=date.today(), subject=subject),
        school_class_id=school_class.id,
        created_by_teacher_id=teacher.id
    )

    # Create another teacher and get their token
    other_teacher_email = "other_teacher@example.com"
    other_teacher_pass = "otherpass"
    other_teacher = crud.crud_user.get_user_by_email(db, email=other_teacher_email)
    if not other_teacher:
        other_teacher_in = schemas.UserCreate(email=other_teacher_email, password=other_teacher_pass, full_name="Other Teacher", role="teacher", roll_number="TEACHER_002")
        hashed_password = get_password_hash(other_teacher_pass)
        other_teacher = crud.crud_user.create_user(db, user_in=other_teacher_in, password_hash=hashed_password)

    other_teacher_headers = get_auth_headers(client, other_teacher_email, other_teacher_pass)

    update_data = {"title": "Unauthorized Update"}
    response = client.put(
        f"{settings.API_V1_STR}/teachers/tasks/{task.id}",
        json=update_data,
        headers=other_teacher_headers
    )
    assert response.status_code == 403


def test_teacher_delete_task_success(client: TestClient, test_teacher_direct_fixture: dict, assigned_teacher_to_class_subject, db: Session):
    teacher, school_class, subject = assigned_teacher_to_class_subject
    task = crud.crud_task.create_task(
        db=db,
        task_in=schemas.TaskCreate(title="To Be Deleted", description="Desc", due_date=date.today(), subject=subject),
        school_class_id=school_class.id,
        created_by_teacher_id=teacher.id
    )
    response = client.delete(
        f"{settings.API_V1_STR}/teachers/tasks/{task.id}",
        headers=test_teacher_direct_fixture
    )
    assert response.status_code == 200
    assert crud.crud_task.get_task(db, task_id=task.id) is None


def test_teacher_delete_task_unauthorized_teacher(client: TestClient, assigned_teacher_to_class_subject, db: Session):
    teacher, school_class, subject = assigned_teacher_to_class_subject
    task = crud.crud_task.create_task(
        db=db,
        task_in=schemas.TaskCreate(title="Protected Task", description="Desc", due_date=date.today(), subject=subject),
        school_class_id=school_class.id,
        created_by_teacher_id=teacher.id
    )

    other_teacher_email = "another_teacher@example.com"
    other_teacher_pass = "anotherpass"
    other_teacher = crud.crud_user.get_user_by_email(db, email=other_teacher_email)
    if not other_teacher:
        other_teacher_in = schemas.UserCreate(email=other_teacher_email, password=other_teacher_pass, full_name="Another Teacher", role="teacher", roll_number="TEACHER_003")
        hashed_password = get_password_hash(other_teacher_pass)
        other_teacher = crud.crud_user.create_user(db, user_in=other_teacher_in, password_hash=hashed_password)

    other_teacher_headers = get_auth_headers(client, other_teacher_email, other_teacher_pass)

    response = client.delete(
        f"{settings.API_V1_STR}/teachers/tasks/{task.id}",
        headers=other_teacher_headers
    )
    assert response.status_code == 403
    assert crud.crud_task.get_task(db, task_id=task.id) is not None


# --- Announcement Endpoints Tests ---

def test_teacher_create_announcement_success_class_specific(client: TestClient, test_teacher_direct_fixture: dict, assigned_teacher_to_class_subject):
    teacher, school_class, subject = assigned_teacher_to_class_subject
    announcement_data = {
        "title": "Math Class Announcement",
        "content": "Reminder: Math test on Friday.",
        "subject": subject,
        "school_class_id": school_class.id  # Correctly pass school_class_id
    }
    response = client.post(
        f"{settings.API_V1_STR}/teachers/announcements",  # Correct endpoint
        json=announcement_data,
        headers=test_teacher_direct_fixture
    )
    assert response.status_code == 201
    content = response.json()
    assert content["title"] == announcement_data["title"]
    assert content["school_class_id"] == school_class.id
    assert content["created_by_user_id"] == teacher.id
    assert content["is_school_wide"] is False


def test_teacher_create_announcement_forbidden_school_wide(client: TestClient, test_teacher_direct_fixture: dict, assigned_teacher_to_class_subject):
    teacher, school_class, subject = assigned_teacher_to_class_subject
    announcement_data = {
        "title": "School-Wide Announcement Attempt",
        "content": "This should not be allowed.",
        "is_school_wide": True,
        "school_class_id": school_class.id
    }
    response = client.post(
        f"{settings.API_V1_STR}/teachers/announcements",
        json=announcement_data,
        headers=test_teacher_direct_fixture
    )
    assert response.status_code == 403


def test_teacher_get_class_announcements_success(client: TestClient, test_teacher_direct_fixture: dict, assigned_teacher_to_class_subject, db: Session):
    teacher, school_class, subject = assigned_teacher_to_class_subject
    # Create an announcement first
    announcement_in = schemas.AnnouncementCreate(
        title="Test Announcement",
        content="This is a test.",
        subject=subject,
        school_class_id=school_class.id
    )
    crud.crud_announcement.create_announcement(db=db, announcement_in=announcement_in, created_by_user_id=teacher.id)

    response = client.get(
        f"{settings.API_V1_STR}/teachers/classes/{school_class.class_code}/announcements",
        headers=test_teacher_direct_fixture
    )
    assert response.status_code == 200
    content = response.json()
    assert len(content) >= 1
    assert any(ann["title"] == "Test Announcement" for ann in content)


def test_teacher_update_announcement_success(client: TestClient, test_teacher_direct_fixture: dict, assigned_teacher_to_class_subject, db: Session):
    teacher, school_class, subject = assigned_teacher_to_class_subject
    announcement = crud.crud_announcement.create_announcement(
        db=db,
        announcement_in=schemas.AnnouncementCreate(title="Original Announcement", content="Original content", subject=subject, school_class_id=school_class.id),
        created_by_user_id=teacher.id
    )
    update_data = {"content": "Updated announcement content."}
    response = client.put(
        f"{settings.API_V1_STR}/teachers/announcements/{announcement.id}",
        json=update_data,
        headers=test_teacher_direct_fixture
    )
    assert response.status_code == 200
    content = response.json()
    assert content["content"] == "Updated announcement content."


def test_teacher_delete_announcement_success(client: TestClient, test_teacher_direct_fixture: dict, assigned_teacher_to_class_subject, db: Session):
    teacher, school_class, subject = assigned_teacher_to_class_subject
    announcement = crud.crud_announcement.create_announcement(
        db=db,
        announcement_in=schemas.AnnouncementCreate(title="To Delete", content="Delete me", subject=subject, school_class_id=school_class.id),
        created_by_user_id=teacher.id
    )
    response = client.delete(
        f"{settings.API_V1_STR}/teachers/announcements/{announcement.id}",
        headers=test_teacher_direct_fixture
    )
    assert response.status_code == 200
    assert crud.crud_announcement.get_announcement(db, announcement_id=announcement.id) is None
