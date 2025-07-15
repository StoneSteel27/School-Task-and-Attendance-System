import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import date, timedelta
import uuid

from app import crud, models, schemas
from app.core.config import settings
from app.core.security import get_password_hash # NEW

# Helper fixture to create a teacher user
@pytest.fixture(scope="function")
def test_teacher_user(db: Session) -> models.User:
    email = "testteacher@example.com"
    password = "testteacherpass"
    roll_number = "TEACHER_001"
    full_name = "Test Teacher"

    user = crud.crud_user.get_user_by_email(db, email=email)
    if not user:
        user_in_create = schemas.UserCreate(
            email=email,
            password=password,
            full_name=full_name,
            roll_number=roll_number,
            is_superuser=False,
            is_active=True,
            role="teacher"
        )
        hashed_password = get_password_hash(password)
        user = crud.crud_user.create_user(db=db, user_in=user_in_create, password_hash=hashed_password)
    else:
        user.is_superuser = False
        user.is_active = True
        user.role = "teacher"
        db.add(user)
        db.commit()
        db.refresh(user)
    return user

# Helper fixture to get teacher token headers
@pytest.fixture(scope="function")
def teacher_token_headers(client: TestClient, test_teacher_user: models.User) -> dict[str, str]:
    login_data = {
        "username": test_teacher_user.email,
        "password": "testteacherpass",
    }
    r = client.post(f"{settings.API_V1_STR}/auth/login/access-token", data=login_data)
    response_json = r.json()
    assert r.status_code == 200, f"Failed to log in teacher for token generation: {response_json}"
    token = response_json["access_token"]
    return {"Authorization": f"Bearer {token}"}

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

def test_teacher_create_task_success(client: TestClient, teacher_token_headers: dict, assigned_teacher_to_class_subject):
    teacher, school_class, subject = assigned_teacher_to_class_subject
    task_data = {
        "title": "Algebra Homework",
        "description": "Complete exercises 1-10 from Chapter 3.",
        "due_date": (date.today() + timedelta(days=7)).isoformat(),
        "subject": subject
    }
    response = client.post(
        f"{settings.API_V1_STR}/teacher/classes/{school_class.class_code}/tasks",
        json=task_data,
        headers=teacher_token_headers
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
        f"{settings.API_V1_STR}/teacher/classes/{test_school_class.class_code}/tasks",
        json=task_data,
        headers=normal_user_token_headers
    )
    assert response.status_code == 403


def test_teacher_create_task_class_not_found(client: TestClient, teacher_token_headers: dict):
    task_data = {
        "title": "Algebra Homework",
        "description": "Complete exercises 1-10 from Chapter 3.",
        "due_date": (date.today() + timedelta(days=7)).isoformat(),
        "subject": "Mathematics"
    }
    response = client.post(
        f"{settings.API_V1_STR}/teacher/classes/NONEXISTENT-CLASS/tasks",
        json=task_data,
        headers=teacher_token_headers
    )
    assert response.status_code == 404


def test_teacher_create_task_not_assigned_to_subject(client: TestClient, teacher_token_headers: dict, test_school_class: models.SchoolClass):
    # Teacher is not assigned to any subject in this class
    task_data = {
        "title": "Algebra Homework",
        "description": "Complete exercises 1-10 from Chapter 3.",
        "due_date": (date.today() + timedelta(days=7)).isoformat(),
        "subject": "Physics" # Teacher is not assigned to Physics
    }
    response = client.post(
        f"{settings.API_V1_STR}/teacher/classes/{test_school_class.class_code}/tasks",
        json=task_data,
        headers=teacher_token_headers
    )
    assert response.status_code == 403


def test_teacher_get_tasks_for_class_success(client: TestClient, teacher_token_headers: dict, assigned_teacher_to_class_subject, db: Session):
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
        f"{settings.API_V1_STR}/teacher/classes/{school_class.class_code}/tasks",
        headers=teacher_token_headers
    )
    assert response.status_code == 200
    content = response.json()
    assert len(content) >= 1
    assert any(task["title"] == "Math Test Prep" for task in content)


def test_teacher_get_tasks_for_class_filter_by_subject(client: TestClient, teacher_token_headers: dict, assigned_teacher_to_class_subject, db: Session):
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
        f"{settings.API_V1_STR}/teacher/classes/{school_class.class_code}/tasks?subject={math_subject}",
        headers=teacher_token_headers
    )
    assert response.status_code == 200
    content = response.json()
    assert len(content) == 1
    assert content[0]["title"] == "Math Homework"
    assert content[0]["subject"] == math_subject


def test_teacher_update_task_success(client: TestClient, teacher_token_headers: dict, assigned_teacher_to_class_subject, db: Session):
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
        f"{settings.API_V1_STR}/teacher/tasks/{created_task.id}",
        json=update_data,
        headers=teacher_token_headers
    )
    assert response.status_code == 200
    content = response.json()
    assert content["title"] == update_data["title"]
    assert content["description"] == update_data["description"]


def test_teacher_update_task_unauthorized_teacher(client: TestClient, teacher_token_headers: dict, test_school_class: models.SchoolClass, db: Session):
    # Create a task by a different teacher (not the one associated with teacher_token_headers)
    other_teacher_email = "otherteacher@example.com"
    other_teacher_pass = "otherteacherpass"
    other_teacher_roll = "TEACHER_002"
    from app.core.security import get_password_hash
    other_teacher = crud.crud_user.create_user(
        db=db,
        user_in=schemas.UserCreate(email=other_teacher_email, password=other_teacher_pass, roll_number=other_teacher_roll, role="teacher"),
        password_hash=get_password_hash(other_teacher_pass)
    )
    crud.crud_teacher_assignment.assign_teacher_to_class_subject(db, teacher=other_teacher, school_class=test_school_class, subject="Mathematics")

    task_data = schemas.TaskCreate(
        title="Other Teacher's Task",
        description="",
        due_date=date.today() + timedelta(days=7),
        subject="Mathematics"
    )
    created_task = crud.crud_task.create_task(db=db, task_in=task_data, school_class_id=test_school_class.id, created_by_teacher_id=other_teacher.id)

    update_data = {"title": "Attempted Update"}
    response = client.put(
        f"{settings.API_V1_STR}/teacher/tasks/{created_task.id}",
        json=update_data,
        headers=teacher_token_headers # This teacher is not the creator
    )
    assert response.status_code == 403


def test_teacher_delete_task_success(client: TestClient, teacher_token_headers: dict, assigned_teacher_to_class_subject, db: Session):
    teacher, school_class, subject = assigned_teacher_to_class_subject
    task_data = schemas.TaskCreate(
        title="Task to Delete",
        description="",
        due_date=date.today() + timedelta(days=7),
        subject=subject
    )
    created_task = crud.crud_task.create_task(db=db, task_in=task_data, school_class_id=school_class.id, created_by_teacher_id=teacher.id)

    response = client.delete(
        f"{settings.API_V1_STR}/teacher/tasks/{created_task.id}",
        headers=teacher_token_headers
    )
    assert response.status_code == 200
    content = response.json()
    assert content["id"] == created_task.id

    # Verify it's actually deleted
    get_response = client.get(
        f"{settings.API_V1_STR}/teacher/classes/{school_class.class_code}/tasks",
        headers=teacher_token_headers
    )
    assert get_response.status_code == 200
    assert not any(task["id"] == created_task.id for task in get_response.json())


def test_teacher_delete_task_unauthorized_teacher(client: TestClient, teacher_token_headers: dict, test_school_class: models.SchoolClass, db: Session):
    # Create a task by a different teacher
    other_teacher_email = "anotherteacher@example.com"
    other_teacher_pass = "anotherteacherpass"
    other_teacher_roll = "TEACHER_003"
    from app.core.security import get_password_hash
    other_teacher = crud.crud_user.create_user(
        db=db,
        user_in=schemas.UserCreate(email=other_teacher_email, password=other_teacher_pass, roll_number=other_teacher_roll, role="teacher"),
        password_hash=get_password_hash(other_teacher_pass)
    )
    crud.crud_teacher_assignment.assign_teacher_to_class_subject(db, teacher=other_teacher, school_class=test_school_class, subject="Mathematics")

    task_data = schemas.TaskCreate(
        title="Other Teacher's Task to Delete",
        description="",
        due_date=date.today() + timedelta(days=7),
        subject="Mathematics"
    )
    created_task = crud.crud_task.create_task(db=db, task_in=task_data, school_class_id=test_school_class.id, created_by_teacher_id=other_teacher.id)

    response = client.delete(
        f"{settings.API_V1_STR}/teacher/tasks/{created_task.id}",
        headers=teacher_token_headers # This teacher is not the creator
    )
    assert response.status_code == 403


# --- Announcement Endpoints Tests ---

def test_teacher_create_announcement_success_class_specific(client: TestClient, teacher_token_headers: dict, assigned_teacher_to_class_subject):
    teacher, school_class, subject = assigned_teacher_to_class_subject
    announcement_data = {
        "title": "Class Meeting",
        "content": "Mandatory class meeting tomorrow at 10 AM.",
        "is_school_wide": False,
        "school_class_id": school_class.id,
        "subject": subject
    }
    response = client.post(
        f"{settings.API_V1_STR}/teacher/announcements",
        json=announcement_data,
        headers=teacher_token_headers
    )
    assert response.status_code == 201
    content = response.json()
    assert content["title"] == announcement_data["title"]
    assert content["school_class_id"] == school_class.id
    assert content["created_by_user_id"] == teacher.id
    assert content["is_school_wide"] is False


def test_teacher_create_announcement_forbidden_school_wide(client: TestClient, teacher_token_headers: dict, test_school_class: models.SchoolClass):
    announcement_data = {
        "title": "School Holiday",
        "content": "School will be closed next Monday.",
        "is_school_wide": True,
        "school_class_id": None, # Should be None for school-wide
        "subject": None
    }
    response = client.post(
        f"{settings.API_V1_STR}/teacher/announcements",
        json=announcement_data,
        headers=teacher_token_headers
    )
    assert response.status_code == 403 # Teachers cannot create school-wide announcements


def test_teacher_get_class_announcements_success(client: TestClient, teacher_token_headers: dict, assigned_teacher_to_class_subject, db: Session):
    teacher, school_class, subject = assigned_teacher_to_class_subject
    # Create an announcement for the class
    announcement_data = schemas.AnnouncementCreate(
        title="Exam Reminder",
        content="Exams start next week.",
        is_school_wide=False,
        school_class_id=school_class.id,
        subject=subject
    )
    crud.crud_announcement.create_announcement(db=db, announcement_in=announcement_data, created_by_user_id=teacher.id)

    response = client.get(
        f"{settings.API_V1_STR}/teacher/classes/{school_class.class_code}/announcements",
        headers=teacher_token_headers
    )
    assert response.status_code == 200
    content = response.json()
    assert len(content) >= 1
    assert any(announcement["title"] == "Exam Reminder" for announcement in content)


def test_teacher_update_announcement_success(client: TestClient, teacher_token_headers: dict, assigned_teacher_to_class_subject, db: Session):
    teacher, school_class, subject = assigned_teacher_to_class_subject
    announcement_data = schemas.AnnouncementCreate(
        title="Original Announcement",
        content="Original Content",
        is_school_wide=False,
        school_class_id=school_class.id,
        subject=subject
    )
    created_announcement = crud.crud_announcement.create_announcement(db=db, announcement_in=announcement_data, created_by_user_id=teacher.id)

    update_data = {"title": "Updated Announcement Title", "content": "New Content"}
    response = client.put(
        f"{settings.API_V1_STR}/teacher/announcements/{created_announcement.id}",
        json=update_data,
        headers=teacher_token_headers
    )
    assert response.status_code == 200
    content = response.json()
    assert content["title"] == update_data["title"]
    assert content["content"] == update_data["content"]


def test_teacher_delete_announcement_success(client: TestClient, teacher_token_headers: dict, assigned_teacher_to_class_subject, db: Session):
    teacher, school_class, subject = assigned_teacher_to_class_subject
    announcement_data = schemas.AnnouncementCreate(
        title="Announcement to Delete",
        content="",
        is_school_wide=False,
        school_class_id=school_class.id,
        subject=subject
    )
    created_announcement = crud.crud_announcement.create_announcement(db=db, announcement_in=announcement_data, created_by_user_id=teacher.id)

    response = client.delete(
        f"{settings.API_V1_STR}/teacher/announcements/{created_announcement.id}",
        headers=teacher_token_headers
    )
    assert response.status_code == 200
    content = response.json()
    assert content["id"] == created_announcement.id

    # Verify it's actually deleted
    get_response = client.get(
        f"{settings.API_V1_STR}/teacher/classes/{school_class.class_code}/announcements",
        headers=teacher_token_headers
    )
    assert get_response.status_code == 200
    assert not any(announcement["id"] == created_announcement.id for announcement in get_response.json())
