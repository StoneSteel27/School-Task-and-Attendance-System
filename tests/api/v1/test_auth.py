# tests/api/v1/test_auth.py
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session as SQLAlchemySession  # Renamed in conftest.py, using it here for type hinting

from app.core.config import settings
from app.models.user import User as UserModel


# The client, db, test_superuser, and test_normal_user fixtures are automatically
# injected by pytest if they are listed as arguments in the test functions.

def test_login_superuser_success(
        client: TestClient, test_superuser: UserModel, db: SQLAlchemySession
):
    """
    Test successful login for an active superuser.
    """
    login_data = {
        "username": test_superuser.email,
        "password": settings.FIRST_SUPERUSER_PASSWORD or "testadminpass",  # Password used in conftest
    }
    response = client.post(f"{settings.API_V1_STR}/auth/login/access-token", data=login_data)

    assert response.status_code == 200
    token_data = response.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"


def test_login_normal_user_success(
        client: TestClient, test_normal_user: UserModel, db: SQLAlchemySession
):
    """
    Test successful login for an active normal user.
    """
    login_data = {
        "username": test_normal_user.email,
        "password": "testuserpass",  # Password used in conftest for normal_user
    }
    response = client.post(f"{settings.API_V1_STR}/auth/login/access-token", data=login_data)

    assert response.status_code == 200
    token_data = response.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"


def test_login_incorrect_password(
        client: TestClient, test_normal_user: UserModel
):
    """
    Test login attempt with a correct email but incorrect password.
    """
    login_data = {
        "username": test_normal_user.email,
        "password": "wrongpassword123",
    }
    response = client.post(f"{settings.API_V1_STR}/auth/login/access-token", data=login_data)

    assert response.status_code == 401  # Unauthorized
    error_data = response.json()
    assert error_data["detail"] == "Incorrect email or password"


def test_login_non_existent_email(
        client: TestClient
):
    """
    Test login attempt with an email that does not exist in the system.
    """
    login_data = {
        "username": "nonexistentuser@example.com",
        "password": "anypassword",
    }
    response = client.post(f"{settings.API_V1_STR}/auth/login/access-token", data=login_data)

    assert response.status_code == 401  # Unauthorized
    error_data = response.json()
    assert error_data["detail"] == "Incorrect email or password"


def test_login_inactive_user(
        client: TestClient, test_normal_user: UserModel, db: SQLAlchemySession
):
    """
    Test login attempt for a user who is marked as inactive.
    """
    # Ensure the user is initially active (though fixture should ensure this)
    assert test_normal_user.is_active

    # Deactivate the user for this test
    test_normal_user.is_active = False
    db.add(test_normal_user)
    db.commit()
    db.refresh(test_normal_user)

    login_data = {
        "username": test_normal_user.email,
        "password": "testuserpass",  # Correct password for the user
    }
    response = client.post(f"{settings.API_V1_STR}/auth/login/access-token", data=login_data)

    assert response.status_code == 400  # Bad Request
    error_data = response.json()
    assert error_data["detail"] == "Inactive user"

    # Teardown: It's good practice to revert state if the fixture scope is wider than 'function'
    # or if other tests might rely on this user being active.
    # However, our 'db' fixture has function scope and rolls back transactions,
    # so this explicit re-activation might not be strictly necessary for *this specific setup*
    # if test_normal_user is re-fetched or re-created by its fixture in subsequent tests.
    # But, if test_normal_user object itself is cached across tests within a module (if its fixture scope was 'module'), this would be vital.
    # Given `test_normal_user` is function-scoped, it's recreated each time.
    # The rollback in the `db` fixture handles cleaning up the change to `is_active`.
    # So, explicit re-activation below is more for illustration or safety in other fixture configurations.
    #
    # test_normal_user.is_active = True
    # db.add(test_normal_user)
    # db.commit()
    # db.refresh(test_normal_user)