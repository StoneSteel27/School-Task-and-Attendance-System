# tests/api/v1/test_users.py
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.user import User as UserModel  # To compare response against the user model
from app.schemas.user import User as UserSchema  # The response schema


# Fixtures normal_user_token_headers, superuser_token_headers,
# test_normal_user, test_superuser are automatically injected by pytest.

def test_read_users_me_normal_user(
        client: TestClient,
        normal_user_token_headers: dict[str, str],
        test_normal_user: UserModel
):
    """
    Test GET /users/me for a normal authenticated user.
    """
    response = client.get(
        f"{settings.API_V1_STR}/users/me",
        headers=normal_user_token_headers
    )
    assert response.status_code == 200
    current_user_data = response.json()

    assert current_user_data["email"] == test_normal_user.email
    assert current_user_data["roll_number"] == test_normal_user.roll_number
    assert current_user_data["full_name"] == test_normal_user.full_name
    assert current_user_data["is_active"] == test_normal_user.is_active
    assert current_user_data["is_superuser"] == test_normal_user.is_superuser
    assert current_user_data["role"] == test_normal_user.role
    assert current_user_data["id"] == test_normal_user.id
    # Check if the response conforms to the User schema (optional, but good)
    UserSchema.model_validate(current_user_data)


def test_read_users_me_superuser(
        client: TestClient,
        superuser_token_headers: dict[str, str],
        test_superuser: UserModel
):
    """
    Test GET /users/me for an authenticated superuser.
    """
    response = client.get(
        f"{settings.API_V1_STR}/users/me",
        headers=superuser_token_headers
    )
    assert response.status_code == 200
    current_user_data = response.json()

    assert current_user_data["email"] == test_superuser.email
    assert current_user_data["roll_number"] == test_superuser.roll_number
    assert current_user_data["full_name"] == test_superuser.full_name
    assert current_user_data["is_active"] == test_superuser.is_active
    assert current_user_data["is_superuser"] == test_superuser.is_superuser
    assert current_user_data["role"] == test_superuser.role
    assert current_user_data["id"] == test_superuser.id
    UserSchema.model_validate(current_user_data)


def test_read_users_me_no_token(
        client: TestClient
):
    """
    Test GET /users/me without providing an authentication token.
    """
    response = client.get(f"{settings.API_V1_STR}/users/me")

    assert response.status_code == 401  # Unauthorized
    error_data = response.json()
    # The exact detail message might vary slightly based on FastAPI's default for missing token
    # "Not authenticated" is common for OAuth2PasswordBearer when token is missing
    assert error_data["detail"] == "Not authenticated"


def test_read_users_me_invalid_token_format(
        client: TestClient
):
    """
    Test GET /users/me with an improperly formatted or invalid token.
    """
    headers = {"Authorization": "Bearer invalidtokenstring"}
    response = client.get(f"{settings.API_V1_STR}/users/me", headers=headers)

    assert response.status_code == 401  # Unauthorized
    error_data = response.json()
    # This message comes from our decode_token function's credentials_exception
    assert error_data["detail"] == "Could not validate credentials"


def test_read_users_me_inactive_user_token(
    client: TestClient,
    test_normal_user: UserModel,
    db: Session # <--- CORRECTED TYPE HINT TO USE THE IMPORTED Session
):
    """
    Test GET /users/me with a token from a user who has been subsequently deactivated.
    The get_current_active_user dependency should catch this.
    """
    # Get a valid token for the user first while they are active
    login_data = {
        "username": test_normal_user.email,
        "password": "testuserpass",
    }
    r = client.post(f"{settings.API_V1_STR}/auth/login/access-token", data=login_data)
    assert r.status_code == 200, f"Login failed during setup: {r.json()}"
    token = r.json()["access_token"]
    active_user_headers = {"Authorization": f"Bearer {token}"}

    # Now, deactivate the user in the database
    test_normal_user.is_active = False
    db.add(test_normal_user)
    db.commit()
    db.refresh(test_normal_user)

    # Attempt to access /users/me with the token obtained when the user was active
    response = client.get(
        f"{settings.API_V1_STR}/users/me",
        headers=active_user_headers
    )

    assert response.status_code == 400 # Bad Request, as per get_current_active_user
    error_data = response.json()
    assert error_data["detail"] == "Inactive user"