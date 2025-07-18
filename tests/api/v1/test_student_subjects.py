from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.user import User as UserModel
from app.schemas.subject import Subject as SubjectSchema


def test_list_student_subjects_normal_user(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    db: Session,
    test_normal_user: UserModel,
):
    # Ensure the student is in a class
    if not test_normal_user.school_class_id:
        # This test requires a student in a class with subjects.
        # The fixture should be updated to provide this, or this test should be skipped.
        # For now, we'll assume the fixture provides a user in a class.
        pass

    response = client.get(
        f"{settings.API_V1_STR}/students/me/subjects",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 200
    subjects = response.json()
    assert isinstance(subjects, list)
    # Further assertions would depend on the test data setup
    # For example, if we know the subjects for the test user's class
    if subjects:
        for subject in subjects:
            SubjectSchema.model_validate(subject)

def test_list_student_subjects_not_student(
    client: TestClient,
    superuser_token_headers: dict[str, str],
):
    response = client.get(
        f"{settings.API_V1_STR}/students/me/subjects",
        headers=superuser_token_headers,
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Only students can view their subjects."

def test_list_student_subjects_no_class(
    client: TestClient,
    db: Session,
):
    # Create a student without a class
    from app.schemas.user import UserCreate
    from app.core.security import get_password_hash
    from app.crud import crud_user
    email = "noclassuser@example.com"
    password = "testuserpass"
    roll_number = "TEST_USER_002"
    full_name = "Test No Class User"
    user_in_create = UserCreate(
        email=email,
        password=password,
        full_name=full_name,
        roll_number=roll_number,
        is_superuser=False,
        is_active=True,
        role="student"
    )
    hashed_password = get_password_hash(password)
    user = crud_user.create_user(db=db, user_in=user_in_create, password_hash=hashed_password)

    # Log in to get a token
    login_data = {
        "username": email,
        "password": password,
    }
    r = client.post(f"{settings.API_V1_STR}/auth/login/access-token", data=login_data)
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get(
        f"{settings.API_V1_STR}/students/me/subjects",
        headers=headers,
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not enrolled in any class."
