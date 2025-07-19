import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import uuid

from app import crud, models, schemas
from app.core.config import settings
from app.core.security import get_password_hash

# Re-using the test_teacher_user fixture from conftest or another test file is ideal,
# but for a standalone example, we define it here. Assume it's available via imports.
# from tests.api.v1.test_teacher_tasks_announcements import test_teacher_user, teacher_token_headers, test_school_class

# To make this file runnable on its own, let's define the necessary fixtures.
# In a real scenario, these would be in conftest.py

@pytest.fixture(scope="function")
def test_teacher_user_for_search(db: Session) -> models.User:
    email = f"search_teacher_{uuid.uuid4().hex[:6]}@example.com"
    password = "securepassword"
    roll_number = f"TEACHER_{uuid.uuid4().hex[:6]}"
    user_in_create = schemas.UserCreate(
        email=email, password=password, full_name="Search Teacher", roll_number=roll_number, role="teacher"
    )
    hashed_password = get_password_hash(password)
    user = crud.crud_user.create_user(db=db, user_in=user_in_create, password_hash=hashed_password)
    return user

@pytest.fixture(scope="function")
def teacher_token_headers_for_search(client: TestClient, test_teacher_user_for_search: models.User) -> dict[str, str]:
    login_data = {"username": test_teacher_user_for_search.email, "password": "securepassword"}
    r = client.post(f"{settings.API_V1_STR}/auth/login/access-token", data=login_data)
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture(scope="function")
def setup_students_and_classes(db: Session, test_teacher_user_for_search: models.User):
    # Create two classes
    class_a_in = schemas.SchoolClassCreate(class_code=f"CLS-A-{uuid.uuid4().hex[:4]}", name="Class A", grade="10", section="A")
    class_b_in = schemas.SchoolClassCreate(class_code=f"CLS-B-{uuid.uuid4().hex[:4]}", name="Class B", grade="11", section="B")
    class_a = crud.crud_school_class.create_school_class(db=db, class_in=class_a_in)
    class_b = crud.crud_school_class.create_school_class(db=db, class_in=class_b_in)

    # Assign teacher to Class A only
    crud.crud_teacher_assignment.assign_teacher_to_class_subject(db, teacher=test_teacher_user_for_search, school_class=class_a, subject="History")

    # Create students
    student1_in = schemas.UserCreate(email=f"student1_{uuid.uuid4().hex[:6]}@example.com", password="pw", roll_number="S1", full_name="Alice Smith")
    student2_in = schemas.UserCreate(email=f"student2_{uuid.uuid4().hex[:6]}@example.com", password="pw", roll_number="S2", full_name="Bob Johnson")
    student3_in = schemas.UserCreate(email=f"student3_{uuid.uuid4().hex[:6]}@example.com", password="pw", roll_number="S3", full_name="Charlie Brown")

    student1 = crud.crud_user.create_user(db, user_in=student1_in, password_hash=get_password_hash("pw"))
    student2 = crud.crud_user.create_user(db, user_in=student2_in, password_hash=get_password_hash("pw"))
    student3 = crud.crud_user.create_user(db, user_in=student3_in, password_hash=get_password_hash("pw"))

    # Assign students to classes
    crud.crud_user.assign_student_to_class(db, student=student1, school_class=class_a) # In teacher's class
    crud.crud_user.assign_student_to_class(db, student=student2, school_class=class_a) # In teacher's class
    crud.crud_user.assign_student_to_class(db, student=student3, school_class=class_b) # NOT in teacher's class

    db.commit()
    return {"class_a": class_a, "class_b": class_b, "student1": student1, "student2": student2, "student3": student3}


def test_search_students_no_params_fails(client: TestClient, teacher_token_headers_for_search: dict):
    response = client.get(f"{settings.API_V1_STR}/teachers/search", headers=teacher_token_headers_for_search)
    assert response.status_code == 400
    assert "at least one search parameter" in response.json()["detail"].lower()

def test_search_students_by_name_success(client: TestClient, teacher_token_headers_for_search: dict, setup_students_and_classes):
    # Search for "Alice" - should only find student1
    response = client.get(f"{settings.API_V1_STR}/teachers/search?name=Alice", headers=teacher_token_headers_for_search)
    assert response.status_code == 200
    results = response.json()
    assert len(results) == 1
    assert results[0]["full_name"] == "Alice Smith"
    assert results[0]["roll_number"] == "S1"

def test_search_students_by_partial_name(client: TestClient, teacher_token_headers_for_search: dict, setup_students_and_classes):
    # Search for "son" - should only find Bob Johnson (student2) because Charlie is not in the teacher's class
    response = client.get(f"{settings.API_V1_STR}/teachers/search?name=son", headers=teacher_token_headers_for_search)
    assert response.status_code == 200
    results = response.json()
    assert len(results) == 1
    assert results[0]["full_name"] == "Bob Johnson"
    assert results[0]["roll_number"] == "S2"

def test_search_students_by_roll_number_success(client: TestClient, teacher_token_headers_for_search: dict, setup_students_and_classes):
    # Search for roll number "S2"
    response = client.get(f"{settings.API_V1_STR}/teachers/search?roll_number=S2", headers=teacher_token_headers_for_search)
    assert response.status_code == 200
    results = response.json()
    assert len(results) == 1
    assert results[0]["roll_number"] == "S2"

def test_search_students_by_roll_number_not_in_class(client: TestClient, teacher_token_headers_for_search: dict, setup_students_and_classes):
    # Search for roll number "S3" - student exists but is not in the teacher's class
    response = client.get(f"{settings.API_V1_STR}/teachers/search?roll_number=S3", headers=teacher_token_headers_for_search)
    assert response.status_code == 200
    results = response.json()
    assert len(results) == 0 # Should not be found

def test_search_students_by_class_code_success(client: TestClient, teacher_token_headers_for_search: dict, setup_students_and_classes):
    class_a_code = setup_students_and_classes["class_a"].class_code
    response = client.get(f"{settings.API_V1_STR}/teachers/search?class_code={class_a_code}", headers=teacher_token_headers_for_search)
    assert response.status_code == 200
    results = response.json()
    assert len(results) == 2
    roll_numbers = {r["roll_number"] for r in results}
    assert "S1" in roll_numbers
    assert "S2" in roll_numbers

def test_search_students_by_class_code_not_assigned(client: TestClient, teacher_token_headers_for_search: dict, setup_students_and_classes):
    class_b_code = setup_students_and_classes["class_b"].class_code
    # Teacher is not assigned to Class B
    response = client.get(f"{settings.API_V1_STR}/teachers/search?class_code={class_b_code}", headers=teacher_token_headers_for_search)
    assert response.status_code == 200
    results = response.json()
    assert len(results) == 0 # Should not return students from a class they don't teach

def test_search_students_by_name_and_class_code(client: TestClient, teacher_token_headers_for_search: dict, setup_students_and_classes):
    class_a_code = setup_students_and_classes["class_a"].class_code
    # Search for name "Bob" in Class A
    response = client.get(f"{settings.API_V1_STR}/teachers/search?name=Bob&class_code={class_a_code}", headers=teacher_token_headers_for_search)
    assert response.status_code == 200
    results = response.json()
    assert len(results) == 1
    assert results[0]["full_name"] == "Bob Johnson"
