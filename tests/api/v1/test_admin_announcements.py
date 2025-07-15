import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import date, timedelta
import uuid

from app.core.config import settings
from app.core.security import get_password_hash # NEW
from app import crud, models, schemas

# Helper fixture to create a school class (reusing from teacher tests if available, or define here)
@pytest.fixture(scope="function")
def test_school_class_admin(db: Session) -> models.SchoolClass:
    class_in = schemas.SchoolClassCreate(
        class_code=f"ADM-CLS-{uuid.uuid4().hex[:8].upper()}",
        name="Admin Test Class 01",
        grade="7",
        section="A"
    )
    school_class_schema = crud.crud_school_class.create_school_class(db=db, class_in=class_in)
    school_class_orm = crud.crud_school_class.get_school_class_orm_by_class_code(db, class_code=school_class_schema.class_code)
    return school_class_orm

# Helper fixture to create a teacher user (reusing from teacher tests if available, or define here)
@pytest.fixture(scope="function")
def test_teacher_user_admin(db: Session) -> models.User:
    email = "adminteacher@example.com"
    password = "adminteacherpass"
    roll_number = "ADM_TCH_001"
    full_name = "Admin Test Teacher"

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

# Helper to assign teacher to a class and subject
@pytest.fixture(scope="function")
def assigned_teacher_to_class_subject_admin(db: Session, test_teacher_user_admin: models.User, test_school_class_admin: models.SchoolClass):
    crud.crud_teacher_assignment.assign_teacher_to_class_subject(
        db=db, teacher=test_teacher_user_admin, school_class=test_school_class_admin, subject="Science"
    )
    db.refresh(test_teacher_user_admin)
    db.refresh(test_school_class_admin)
    return test_teacher_user_admin, test_school_class_admin, "Science"


# --- Admin Announcement Endpoints Tests ---

def test_admin_create_school_wide_announcement_success(client: TestClient, superuser_token_headers: dict):
    announcement_data = {
        "title": "School-Wide Event",
        "content": "All students are invited to the annual sports day.",
        "is_school_wide": True,
        "school_class_id": None,
        "subject": None
    }
    response = client.post(
        f"{settings.API_V1_STR}/admin/announcements",
        json=announcement_data,
        headers=superuser_token_headers
    )
    assert response.status_code == 201
    content = response.json()
    assert content["title"] == announcement_data["title"]
    assert content["is_school_wide"] is True
    assert content["school_class_id"] is None
    assert content["subject"] is None


def test_admin_create_class_specific_announcement_success(client: TestClient, superuser_token_headers: dict, test_school_class_admin: models.SchoolClass):
    announcement_data = {
        "title": "Class Field Trip Reminder",
        "content": "Don't forget permission slips for the field trip.",
        "is_school_wide": False,
        "school_class_id": test_school_class_admin.id,
        "subject": None
    }
    response = client.post(
        f"{settings.API_V1_STR}/admin/announcements",
        json=announcement_data,
        headers=superuser_token_headers
    )
    assert response.status_code == 201
    content = response.json()
    assert content["title"] == announcement_data["title"]
    assert content["is_school_wide"] is False
    assert content["school_class_id"] == test_school_class_admin.id
    assert content["subject"] is None


def test_admin_create_subject_specific_announcement_success(client: TestClient, superuser_token_headers: dict, test_school_class_admin: models.SchoolClass):
    announcement_data = {
        "title": "Science Project Deadline",
        "content": "Science project is due next Friday.",
        "is_school_wide": False,
        "school_class_id": test_school_class_admin.id,
        "subject": "Science"
    }
    response = client.post(
        f"{settings.API_V1_STR}/admin/announcements",
        json=announcement_data,
        headers=superuser_token_headers
    )
    assert response.status_code == 201
    content = response.json()
    assert content["title"] == announcement_data["title"]
    assert content["is_school_wide"] is False
    assert content["school_class_id"] == test_school_class_admin.id
    assert content["subject"] == "Science"


def test_admin_create_announcement_class_not_found(client: TestClient, superuser_token_headers: dict):
    announcement_data = {
        "title": "Invalid Class Announcement",
        "content": "This should fail.",
        "is_school_wide": False,
        "school_class_id": 99999, # Non-existent ID
        "subject": None
    }
    response = client.post(
        f"{settings.API_V1_STR}/admin/announcements",
        json=announcement_data,
        headers=superuser_token_headers
    )
    assert response.status_code == 404


def test_admin_get_all_announcements_success(client: TestClient, superuser_token_headers: dict, db: Session, test_school_class_admin: models.SchoolClass):
    # Create a mix of announcements
    crud.crud_announcement.create_announcement(db=db, announcement_in=schemas.AnnouncementCreate(title="Global News", content="", is_school_wide=True), created_by_user_id=1) # Assuming admin user ID 1
    crud.crud_announcement.create_announcement(db=db, announcement_in=schemas.AnnouncementCreate(title="Class News", content="", is_school_wide=False, school_class_id=test_school_class_admin.id), created_by_user_id=1)
    crud.crud_announcement.create_announcement(db=db, announcement_in=schemas.AnnouncementCreate(title="Subject News", content="", is_school_wide=False, school_class_id=test_school_class_admin.id, subject="Science"), created_by_user_id=1)

    response = client.get(
        f"{settings.API_V1_STR}/admin/announcements",
        headers=superuser_token_headers
    )
    assert response.status_code == 200
    content = response.json()
    assert len(content) >= 3 # At least the ones we just created
    assert any(a["title"] == "Global News" for a in content)
    assert any(a["title"] == "Class News" for a in content)
    assert any(a["title"] == "Subject News" for a in content)


def test_admin_get_announcements_filter_school_wide(client: TestClient, superuser_token_headers: dict, db: Session):
    crud.crud_announcement.create_announcement(db=db, announcement_in=schemas.AnnouncementCreate(title="Only School Wide", content="", is_school_wide=True), created_by_user_id=1)
    crud.crud_announcement.create_announcement(db=db, announcement_in=schemas.AnnouncementCreate(title="Not School Wide", content="", is_school_wide=False, school_class_id=1), created_by_user_id=1)

    response = client.get(
        f"{settings.API_V1_STR}/admin/announcements?is_school_wide=true",
        headers=superuser_token_headers
    )
    assert response.status_code == 200
    content = response.json()
    assert len(content) >= 1
    assert all(a["is_school_wide"] is True for a in content)
    assert any(a["title"] == "Only School Wide" for a in content)
    assert not any(a["title"] == "Not School Wide" for a in content)


def test_admin_get_announcements_filter_by_class_code(client: TestClient, superuser_token_headers: dict, db: Session, test_school_class_admin: models.SchoolClass):
    # Create announcements for test_school_class_admin
    crud.crud_announcement.create_announcement(db=db, announcement_in=schemas.AnnouncementCreate(title="Class Specific A", content="", is_school_wide=False, school_class_id=test_school_class_admin.id), created_by_user_id=1)
    # Create an announcement for another class (if needed, for negative test)

    response = client.get(
        f"{settings.API_V1_STR}/admin/announcements?class_code={test_school_class_admin.class_code}",
        headers=superuser_token_headers
    )
    assert response.status_code == 200
    content = response.json()
    assert len(content) >= 1
    assert all(a["school_class_id"] == test_school_class_admin.id and a["is_school_wide"] is False for a in content)
    assert any(a["title"] == "Class Specific A" for a in content)


def test_admin_get_announcements_filter_by_subject_and_class(client: TestClient, superuser_token_headers: dict, db: Session, test_school_class_admin: models.SchoolClass):
    crud.crud_announcement.create_announcement(db=db, announcement_in=schemas.AnnouncementCreate(title="Science Class News", content="", is_school_wide=False, school_class_id=test_school_class_admin.id, subject="Science"), created_by_user_id=1)
    crud.crud_announcement.create_announcement(db=db, announcement_in=schemas.AnnouncementCreate(title="Math Class News", content="", is_school_wide=False, school_class_id=test_school_class_admin.id, subject="Mathematics"), created_by_user_id=1)

    response = client.get(
        f"{settings.API_V1_STR}/admin/announcements?class_code={test_school_class_admin.class_code}&subject=Science",
        headers=superuser_token_headers
    )
    assert response.status_code == 200
    content = response.json()
    assert len(content) >= 1
    assert all(a["school_class_id"] == test_school_class_admin.id and a["subject"] == "Science" for a in content)
    assert any(a["title"] == "Science Class News" for a in content)
    assert not any(a["title"] == "Math Class News" for a in content)


def test_admin_update_announcement_success(client: TestClient, superuser_token_headers: dict, db: Session):
    created_announcement = crud.crud_announcement.create_announcement(db=db, announcement_in=schemas.AnnouncementCreate(title="Old Title", content="Old Content", is_school_wide=True), created_by_user_id=1)

    update_data = {"title": "New Title", "content": "New Content", "is_school_wide": False} # Change to non-school-wide
    response = client.put(
        f"{settings.API_V1_STR}/admin/announcements/{created_announcement.id}",
        json=update_data,
        headers=superuser_token_headers
    )
    assert response.status_code == 200
    content = response.json()
    assert content["title"] == update_data["title"]
    assert content["content"] == update_data["content"]
    assert content["is_school_wide"] is False


def test_admin_update_announcement_change_to_school_wide_from_teacher_created(client: TestClient, superuser_token_headers: dict, test_school_class_admin: models.SchoolClass, test_teacher_user_admin: models.User, db: Session):
    # Teacher creates a class-specific announcement
    teacher_created_announcement = crud.crud_announcement.create_announcement(
        db=db,
        announcement_in=schemas.AnnouncementCreate(title="Teacher Class Ann", content="", is_school_wide=False, school_class_id=test_school_class_admin.id),
        created_by_user_id=test_teacher_user_admin.id
    )

    # Admin tries to change it to school-wide
    update_data = {"is_school_wide": True, "school_class_id": None, "subject": None}
    response = client.put(
        f"{settings.API_V1_STR}/admin/announcements/{teacher_created_announcement.id}",
        json=update_data,
        headers=superuser_token_headers
    )
    assert response.status_code == 200
    content = response.json()
    assert content["is_school_wide"] is True
    assert content["school_class_id"] is None
    assert content["subject"] is None


def test_admin_delete_announcement_success(client: TestClient, superuser_token_headers: dict, db: Session):
    created_announcement = crud.crud_announcement.create_announcement(db=db, announcement_in=schemas.AnnouncementCreate(title="Announcement to Delete", content="", is_school_wide=True), created_by_user_id=1)

    response = client.delete(
        f"{settings.API_V1_STR}/admin/announcements/{created_announcement.id}",
        headers=superuser_token_headers
    )
    assert response.status_code == 200
    content = response.json()
    assert content["id"] == created_announcement.id

    # Verify it's actually deleted
    get_response = client.get(
        f"{settings.API_V1_STR}/admin/announcements",
        headers=superuser_token_headers
    )
    assert get_response.status_code == 200
    assert not any(a["id"] == created_announcement.id for a in get_response.json())
