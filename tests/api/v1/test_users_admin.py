import uuid

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session as SQLAlchemySession
from app.core.config import settings
from app.core.security import get_password_hash, verify_password
from app.models.user import User as UserModel
from app.schemas.user import User as UserSchema
from app.crud import crud_user
from app.schemas.user import UserCreate, UserUpdate


def random_email() -> str:
    return f"{uuid.uuid4().hex[:10]}@example.com"


def random_roll_number(prefix: str = "RN") -> str:
    return f"{prefix}-{uuid.uuid4().hex[:10].upper()}"


def random_password() -> str:
    return f"pwd-{uuid.uuid4().hex[:8]}"


# --- Tests for POST /admin/users/ ---

def test_create_student_user_success_as_superuser(
        client: TestClient, superuser_token_headers: dict[str, str], db: SQLAlchemySession
):
    """
    Test successful creation of a new 'student' user by a superuser.
    """
    email = random_email()
    roll_number = random_roll_number("STUDENT")
    password = random_password()
    full_name = "Test Student Name"

    user_data_in = {
        "email": email,
        "password": password,
        "roll_number": roll_number,
        "full_name": full_name,
        "role": "student",
        "is_active": True,
        "is_superuser": False,
    }

    response = client.post(
        f"{settings.API_V1_STR}/admin/users/",
        headers=superuser_token_headers,
        json=user_data_in,
    )

    assert response.status_code == 201
    created_user_data = response.json()

    assert created_user_data["email"] == email
    assert created_user_data["roll_number"] == roll_number
    assert created_user_data["full_name"] == full_name
    assert created_user_data["role"] == "student"
    assert created_user_data["is_active"] is True
    assert created_user_data["is_superuser"] is False
    assert "id" in created_user_data
    assert "hashed_password" not in created_user_data

    db_user = crud_user.get_user_by_email(db, email=email)
    assert db_user is not None
    assert db_user.roll_number == roll_number
    assert db_user.full_name == full_name
    assert db_user.role == "student"
    assert db_user.is_active is True
    assert db_user.is_superuser is False

    UserSchema.model_validate(created_user_data)


def test_create_teacher_user_success_as_superuser(
        client: TestClient, superuser_token_headers: dict[str, str], db: SQLAlchemySession
):
    """
    Test successful creation of a new 'teacher' user by a superuser.
    """
    email = random_email()
    roll_number = random_roll_number("TEACH")
    password = random_password()
    full_name = "Test Teacher Name"

    user_data_in = {
        "email": email,
        "password": password,
        "roll_number": roll_number,
        "full_name": full_name,
        "role": "teacher",
        "is_active": True,
        "is_superuser": False,
    }

    response = client.post(
        f"{settings.API_V1_STR}/admin/users/",
        headers=superuser_token_headers,
        json=user_data_in,
    )

    assert response.status_code == 201
    created_user_data = response.json()

    assert created_user_data["email"] == email
    assert created_user_data["roll_number"] == roll_number
    assert created_user_data["role"] == "teacher"
    assert created_user_data["is_superuser"] is False

    db_user = crud_user.get_user_by_email(db, email=email)
    assert db_user is not None
    assert db_user.role == "teacher"
    UserSchema.model_validate(created_user_data)


def test_create_admin_user_success_as_superuser(
        client: TestClient, superuser_token_headers: dict[str, str], db: SQLAlchemySession
):
    """
    Test successful creation of a new 'admin' user (also superuser) by a superuser.
    """
    email = random_email()
    roll_number = random_roll_number("ADMIN")
    password = random_password()
    full_name = "Test Admin Name"

    user_data_in = {
        "email": email,
        "password": password,
        "roll_number": roll_number,
        "full_name": full_name,
        "role": "admin",
        "is_active": True,
        "is_superuser": True,
    }

    response = client.post(
        f"{settings.API_V1_STR}/admin/users/",
        headers=superuser_token_headers,
        json=user_data_in,
    )

    assert response.status_code == 201
    created_user_data = response.json()

    assert created_user_data["email"] == email
    assert created_user_data["roll_number"] == roll_number
    assert created_user_data["role"] == "admin"
    assert created_user_data["is_superuser"] is True

    db_user = crud_user.get_user_by_email(db, email=email)
    assert db_user is not None
    assert db_user.role == "admin"
    assert db_user.is_superuser is True
    UserSchema.model_validate(created_user_data)


def test_create_user_as_normal_user_forbidden(
        client: TestClient, normal_user_token_headers: dict[str, str]
):
    """
    Test attempt to create a user by a normal user (should be forbidden).
    """
    user_data_in = {
        "email": random_email(),
        "password": random_password(),
        "roll_number": random_roll_number(),
        "full_name": "Forbidden User",
        "role": "student",
    }
    response = client.post(
        f"{settings.API_V1_STR}/admin/users/",
        headers=normal_user_token_headers,
        json=user_data_in,
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "The user doesn't have enough privileges (not a superuser)"


def test_create_user_no_token_unauthorized(client: TestClient):
    """
    Test attempt to create a user without an authentication token.
    """
    user_data_in = {
        "email": random_email(),
        "password": random_password(),
        "roll_number": random_roll_number(),
        "full_name": "Unauthorized User",
        "role": "student",
    }
    response = client.post(
        f"{settings.API_V1_STR}/admin/users/",
        json=user_data_in,
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_create_user_duplicate_email_as_superuser(
        client: TestClient, superuser_token_headers: dict[str, str], test_normal_user: UserModel
):
    """
    Test attempt to create a user with an email that already exists.
    """
    user_data_in = {
        "email": test_normal_user.email,  # Using existing user's email
        "password": random_password(),
        "roll_number": random_roll_number("DUPEMAIL"),
        "full_name": "Duplicate Email Test",
        "role": "student",
    }
    response = client.post(
        f"{settings.API_V1_STR}/admin/users/",
        headers=superuser_token_headers,
        json=user_data_in,
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "The user with this email already exists in the system."


def test_create_user_duplicate_roll_number_as_superuser(
        client: TestClient, superuser_token_headers: dict[str, str], test_normal_user: UserModel
):
    """
    Test attempt to create a user with a roll number that already exists.
    """
    user_data_in = {
        "email": random_email(),
        "password": random_password(),
        "roll_number": test_normal_user.roll_number,  # Using existing user's roll_number
        "full_name": "Duplicate Roll Number Test",
        "role": "student",
    }
    response = client.post(
        f"{settings.API_V1_STR}/admin/users/",
        headers=superuser_token_headers,
        json=user_data_in,
    )
    assert response.status_code == 400
    assert response.json()[
               "detail"] == f"The user with roll number '{test_normal_user.roll_number}' already exists in the system."


def test_create_user_missing_required_fields_as_superuser(
        client: TestClient, superuser_token_headers: dict[str, str]
):
    """
    Test attempt to create a user with missing required fields (FastAPI should return 422).
    """

    response_missing_email = client.post(
        f"{settings.API_V1_STR}/admin/users/",
        headers=superuser_token_headers,
        json={
            "password": random_password(),
            "roll_number": random_roll_number(),
            "full_name": "Missing Email Test"
        },
    )
    assert response_missing_email.status_code == 422
    assert any(err["loc"] == ["body", "email"] for err in response_missing_email.json()["detail"])

    response_missing_password = client.post(
        f"{settings.API_V1_STR}/admin/users/",
        headers=superuser_token_headers,
        json={
            "email": random_email(),
            "roll_number": random_roll_number(),
            "full_name": "Missing Password Test"
        },
    )
    assert response_missing_password.status_code == 422
    assert any(err["loc"] == ["body", "password"] for err in response_missing_password.json()["detail"])

    # Missing roll_number
    response_missing_roll = client.post(
        f"{settings.API_V1_STR}/admin/users/",
        headers=superuser_token_headers,
        json={
            "email": random_email(),
            "password": random_password(),
            "full_name": "Missing Roll Test"
        },
    )
    assert response_missing_roll.status_code == 422
    assert any(err["loc"] == ["body", "roll_number"] for err in response_missing_roll.json()["detail"])


def test_list_users_success_as_superuser(
        client: TestClient,
        superuser_token_headers: dict[str, str],
        test_superuser: UserModel,
        test_normal_user: UserModel
):
    """
    Test successful retrieval of the users list by a superuser.
    Ensures at least the fixtures users are present.
    """
    response = client.get(
        f"{settings.API_V1_STR}/admin/users/",
        headers=superuser_token_headers
    )
    assert response.status_code == 200
    users_list = response.json()

    assert isinstance(users_list, list)
    # We know at least test_superuser and test_normal_user should exist
    assert len(users_list) >= 2

    found_superuser = False
    found_normal_user = False
    for user_data in users_list:
        UserSchema.model_validate(user_data)
        if user_data["email"] == test_superuser.email:
            found_superuser = True
            assert user_data["roll_number"] == test_superuser.roll_number
            assert user_data["is_superuser"] is True
        elif user_data["email"] == test_normal_user.email:
            found_normal_user = True
            assert user_data["roll_number"] == test_normal_user.roll_number
            assert user_data["is_superuser"] is False

    assert found_superuser, f"Superuser {test_superuser.email} not found in the list."
    assert found_normal_user, f"Normal user {test_normal_user.email} not found in the list."


def test_list_users_pagination_as_superuser(
        client: TestClient, superuser_token_headers: dict[str, str], db: SQLAlchemySession
):
    """
    Test pagination for listing users by a superuser.
    Creates a few users to test skip and limit.
    """

    temp_users_data_for_verification = []
    for i in range(5):
        email = random_email()
        roll_num = random_roll_number(f"PGUSER{i}")
        pwd = random_password()
        full_name = f"Page User {i}"
        role = "student"
        is_active = True
        is_superuser = False

        user_create_schema = UserCreate(
            email=email,
            password=pwd,
            roll_number=roll_num,
            full_name=full_name,
            role=role,
            is_active=is_active,
            is_superuser=is_superuser,
        )

        # The crud_user.create_user expects the plain password in user_in
        # and a separate hashed password. The API endpoint usually does this.
        # Here, we're calling CRUD directly, so we simulate that behavior.
        hashed_pwd = get_password_hash(pwd)

        user_in_db = crud_user.create_user(
            db=db,
            user_in=user_create_schema,
            password_hash=hashed_pwd
        )
        temp_users_data_for_verification.append({"email": email, "roll_number": roll_num, "id": user_in_db.id})

    response_limit = client.get(
        f"{settings.API_V1_STR}/admin/users/?limit=2",
        headers=superuser_token_headers
    )
    assert response_limit.status_code == 200
    users_limit_list = response_limit.json()
    assert len(users_limit_list) <= 2  # Should respect the limit, or be less if fewer users exist

    # Test with skip and limit (assuming users are ordered by roll_number as per crud_user.get_users)

    all_users_response = client.get(f"{settings.API_V1_STR}/admin/users/?limit=100", headers=superuser_token_headers)
    assert all_users_response.status_code == 200
    all_users_list = all_users_response.json()

    if len(all_users_list) > 1:
        response_skip_limit = client.get(
            f"{settings.API_V1_STR}/admin/users/?skip=1&limit=2",
            headers=superuser_token_headers
        )
        assert response_skip_limit.status_code == 200
        users_skip_limit_list = response_skip_limit.json()

        assert len(users_skip_limit_list) <= 2

        if users_skip_limit_list:

            # (because we skipped 1)
            assert users_skip_limit_list[0]["roll_number"] == all_users_list[1]["roll_number"]
            if len(users_skip_limit_list) > 1 and len(all_users_list) > 2:
                assert users_skip_limit_list[1]["roll_number"] == all_users_list[2]["roll_number"]


def test_list_users_as_normal_user_forbidden(
        client: TestClient, normal_user_token_headers: dict[str, str]
):
    """
    Test attempt to list users by a normal user (should be forbidden).
    """
    response = client.get(
        f"{settings.API_V1_STR}/admin/users/",
        headers=normal_user_token_headers
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "The user doesn't have enough privileges (not a superuser)"


def test_list_users_no_token_unauthorized(client: TestClient):
    """
    Test attempt to list users without an authentication token.
    """
    response = client.get(f"{settings.API_V1_STR}/admin/users/")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


# --- Tests for GET /admin/users/{user_roll_number} ---

def test_get_user_by_roll_number_success_as_superuser(
        client: TestClient,
        superuser_token_headers: dict[str, str],
        test_normal_user: UserModel
):
    """
    Test successful retrieval of a specific user by roll number by a superuser.
    """
    target_roll_number = test_normal_user.roll_number
    response = client.get(
        f"{settings.API_V1_STR}/admin/users/{target_roll_number}",
        headers=superuser_token_headers
    )
    assert response.status_code == 200
    user_data = response.json()

    assert user_data["email"] == test_normal_user.email
    assert user_data["roll_number"] == test_normal_user.roll_number
    assert user_data["full_name"] == test_normal_user.full_name
    assert user_data["role"] == test_normal_user.role
    assert user_data["is_active"] == test_normal_user.is_active
    assert user_data["is_superuser"] == test_normal_user.is_superuser
    UserSchema.model_validate(user_data)


def test_get_user_by_roll_number_non_existent_as_superuser(
        client: TestClient, superuser_token_headers: dict[str, str]
):
    """
    Test attempt to retrieve a user by a non-existent roll number by a superuser.
    """
    non_existent_roll_number = random_roll_number("NONEXIST")
    response = client.get(
        f"{settings.API_V1_STR}/admin/users/{non_existent_roll_number}",
        headers=superuser_token_headers
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


def test_get_user_by_roll_number_as_normal_user_forbidden(
        client: TestClient,
        normal_user_token_headers: dict[str, str],
        test_superuser: UserModel  # Trying to fetch another user's details
):
    """
    Test attempt by a normal user to retrieve another user's details by roll number (should be forbidden).
    """
    target_roll_number = test_superuser.roll_number  # Could be any user's roll number
    response = client.get(
        f"{settings.API_V1_STR}/admin/users/{target_roll_number}",
        headers=normal_user_token_headers
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "The user doesn't have enough privileges (not a superuser)"


def test_get_user_by_roll_number_no_token_unauthorized(
        client: TestClient, test_normal_user: UserModel
):
    """
    Test attempt to retrieve a user by roll number without an authentication token.
    """
    target_roll_number = test_normal_user.roll_number
    response = client.get(f"{settings.API_V1_STR}/admin/users/{target_roll_number}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def create_modifiable_test_user(
        db: SQLAlchemySession,
        role: str = "student",
        is_active: bool = True,
        is_superuser: bool = False,
        suffix: str = "MOD"
) -> UserModel:
    email = random_email()
    roll_number = random_roll_number(suffix)
    password = random_password()
    full_name = f"Modifiable {role.capitalize()} User {suffix}"

    user_create_schema = UserCreate(
        email=email,
        password=password,
        roll_number=roll_number,
        full_name=full_name,
        role=role,
        is_active=is_active,
        is_superuser=is_superuser
    )
    hashed_pwd = get_password_hash(password)
    created_user = crud_user.create_user(
        db=db,
        user_in=user_create_schema,
        password_hash=hashed_pwd
    )
    return created_user


def test_update_user_details_success_as_superuser(
        client: TestClient, superuser_token_headers: dict[str, str], db: SQLAlchemySession
):
    """
    Test successful update of various user details by a superuser.
    """
    user_to_update = create_modifiable_test_user(db, role="student", suffix="DETAIL")
    original_roll_number = user_to_update.roll_number

    new_email = random_email()
    new_roll_number = random_roll_number("UPDATEDRN")
    new_full_name = "Updated Full Name by Admin"
    new_role = "teacher"
    new_is_active = False
    new_is_superuser = True
    update_payload = UserUpdate(
        email=new_email,
        roll_number=new_roll_number,
        full_name=new_full_name,
        role=new_role,
        is_active=new_is_active,
        is_superuser=new_is_superuser
    ).model_dump(exclude_unset=True)  # exclude_unset ensures only provided fields are sent

    response = client.put(
        f"{settings.API_V1_STR}/admin/users/{original_roll_number}",
        headers=superuser_token_headers,
        json=update_payload,
    )

    assert response.status_code == 200
    updated_user_data = response.json()

    assert updated_user_data["email"] == new_email
    assert updated_user_data["roll_number"] == new_roll_number
    assert updated_user_data["full_name"] == new_full_name
    assert updated_user_data["role"] == new_role
    assert updated_user_data["is_active"] == new_is_active
    assert updated_user_data["is_superuser"] == new_is_superuser
    assert "hashed_password" not in updated_user_data
    UserSchema.model_validate(updated_user_data)
    # Verify in DB (fetch by the new roll number as it has changed)
    db_user = crud_user.get_user_by_roll_number(db, roll_number=new_roll_number)
    assert db_user is not None
    assert db_user.id == user_to_update.id
    assert db_user.email == new_email
    assert db_user.full_name == new_full_name
    assert db_user.role == new_role
    assert db_user.is_active == new_is_active
    assert db_user.is_superuser == new_is_superuser


def test_update_user_password_success_as_superuser(
        client: TestClient, superuser_token_headers: dict[str, str], db: SQLAlchemySession
):
    """
    Test successful update of a user's password by a superuser.
    """
    user_to_update = create_modifiable_test_user(db, suffix="PASS")
    user_roll_number = user_to_update.roll_number
    original_hashed_password = user_to_update.hashed_password

    new_password = random_password()
    update_payload = UserUpdate(password=new_password).model_dump(exclude_unset=True)

    response = client.put(
        f"{settings.API_V1_STR}/admin/users/{user_roll_number}",
        headers=superuser_token_headers,
        json=update_payload,
    )

    assert response.status_code == 200
    updated_user_data = response.json()
    assert "hashed_password" not in updated_user_data

    db.refresh(user_to_update)
    assert user_to_update.hashed_password != original_hashed_password
    assert verify_password(new_password, user_to_update.hashed_password)


def test_update_user_non_existent_as_superuser(
        client: TestClient, superuser_token_headers: dict[str, str]
):
    """
    Test attempt to update a user that does not exist by a superuser.
    """
    non_existent_roll_number = random_roll_number("NONEX")
    update_payload = UserUpdate(full_name="Ghost User").model_dump(exclude_unset=True)

    response = client.put(
        f"{settings.API_V1_STR}/admin/users/{non_existent_roll_number}",
        headers=superuser_token_headers,
        json=update_payload,
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


def test_update_user_to_duplicate_email_as_superuser(
        client: TestClient, superuser_token_headers: dict[str, str], db: SQLAlchemySession,
        test_normal_user: UserModel  # An existing user whose email we'll try to use
):
    """
    Test attempt to update a user's email to an email that is already in use by another user.
    """
    user_to_update = create_modifiable_test_user(db, suffix="DUPEMAIL")
    user_roll_number = user_to_update.roll_number

    update_payload = UserUpdate(email=test_normal_user.email).model_dump(
        exclude_unset=True)  # Try to use existing user's email

    response = client.put(
        f"{settings.API_V1_STR}/admin/users/{user_roll_number}",
        headers=superuser_token_headers,
        json=update_payload,
    )
    assert response.status_code == 400

    assert "email or roll number may already be in use" in response.json()["detail"].lower()


def test_update_user_to_duplicate_roll_number_as_superuser(
        client: TestClient, superuser_token_headers: dict[str, str], db: SQLAlchemySession,
        test_normal_user: UserModel  # An existing user whose roll_number we'll try to use
):
    """
    Test attempt to update a user's roll_number to one that is already in use by another user.
    """
    user_to_update = create_modifiable_test_user(db, suffix="DUPRN")
    original_roll_number = user_to_update.roll_number

    update_payload = UserUpdate(roll_number=test_normal_user.roll_number).model_dump(exclude_unset=True)

    response = client.put(
        f"{settings.API_V1_STR}/admin/users/{original_roll_number}",
        headers=superuser_token_headers,
        json=update_payload,
    )
    assert response.status_code == 400
    assert "email or roll number may already be in use" in response.json()["detail"].lower()


def test_update_user_as_normal_user_forbidden(
        client: TestClient, normal_user_token_headers: dict[str, str], db: SQLAlchemySession
):
    """
    Test attempt to update a user by a normal user (should be forbidden).
    """
    user_to_update = create_modifiable_test_user(db, suffix="FORBID")
    user_roll_number = user_to_update.roll_number
    update_payload = UserUpdate(full_name="Attempted Update by Normal User").model_dump(exclude_unset=True)

    response = client.put(
        f"{settings.API_V1_STR}/admin/users/{user_roll_number}",
        headers=normal_user_token_headers,
        json=update_payload,
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "The user doesn't have enough privileges (not a superuser)"


def test_update_user_no_token_unauthorized(
        client: TestClient, db: SQLAlchemySession
):
    """
    Test attempt to update a user without an authentication token.
    """
    user_to_update = create_modifiable_test_user(db, suffix="NOTOKEN")
    user_roll_number = user_to_update.roll_number
    update_payload = UserUpdate(full_name="Attempted Update No Token").model_dump(exclude_unset=True)

    response = client.put(
        f"{settings.API_V1_STR}/admin/users/{user_roll_number}",
        json=update_payload,
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_update_user_with_invalid_email_format_as_superuser(
        client: TestClient, superuser_token_headers: dict[str, str], db: SQLAlchemySession
):
    """
    Test attempt to update user with an invalid email format.
    """
    user_to_update = create_modifiable_test_user(db, suffix="INVEMAIL")
    user_roll_number = user_to_update.roll_number

    update_payload = {"email": "not-an-email"}
    response = client.put(
        f"{settings.API_V1_STR}/admin/users/{user_roll_number}",
        headers=superuser_token_headers,
        json=update_payload,
    )
    assert response.status_code == 422
    error_detail = response.json()["detail"]
    assert any(err["loc"] == ["body", "email"] and "valid email address" in err["msg"].lower() for err in error_detail)


def test_delete_user_success_as_superuser(
        client: TestClient, superuser_token_headers: dict[str, str], db: SQLAlchemySession
):
    """
    Test successful deletion of a user by a superuser.
    """
    user_to_delete = create_modifiable_test_user(db, role="student", suffix="DELSUCCESS")
    user_roll_number_to_delete = user_to_delete.roll_number
    user_id_to_delete = user_to_delete.id
    response = client.delete(
        f"{settings.API_V1_STR}/admin/users/{user_roll_number_to_delete}",
        headers=superuser_token_headers,
    )

    assert response.status_code == 200
    deleted_user_data = response.json()

    assert deleted_user_data["roll_number"] == user_roll_number_to_delete
    assert deleted_user_data["email"] == user_to_delete.email
    assert deleted_user_data["id"] == user_id_to_delete
    UserSchema.model_validate(deleted_user_data)

    db_user_after_delete = crud_user.get_user(db, user_id=user_id_to_delete)
    assert db_user_after_delete is None
    db_user_by_roll_after_delete = crud_user.get_user_by_roll_number(db, roll_number=user_roll_number_to_delete)
    assert db_user_by_roll_after_delete is None


def test_delete_user_non_existent_as_superuser(
        client: TestClient, superuser_token_headers: dict[str, str]
):
    """
    Test attempt to delete a user that does not exist by a superuser.
    """
    non_existent_roll_number = random_roll_number("NONEXDEL")

    response = client.delete(
        f"{settings.API_V1_STR}/admin/users/{non_existent_roll_number}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


def test_delete_self_as_superuser_forbidden(
        client: TestClient, superuser_token_headers: dict[str, str], test_superuser: UserModel
):
    """
    Test attempt by a superuser to delete themselves (should be forbidden by endpoint logic).
    """
    self_roll_number = test_superuser.roll_number

    response = client.delete(
        f"{settings.API_V1_STR}/admin/users/{self_roll_number}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Superuser cannot delete themselves."


def test_delete_user_as_normal_user_forbidden(
        client: TestClient, normal_user_token_headers: dict[str, str], db: SQLAlchemySession
):
    """
    Test attempt to delete a user by a normal user (should be forbidden).
    """
    user_to_delete = create_modifiable_test_user(db, suffix="DELFORBID")
    user_roll_number_to_delete = user_to_delete.roll_number

    response = client.delete(
        f"{settings.API_V1_STR}/admin/users/{user_roll_number_to_delete}",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "The user doesn't have enough privileges (not a superuser)"

    db_user_after_attempt = crud_user.get_user_by_roll_number(db, roll_number=user_roll_number_to_delete)
    assert db_user_after_attempt is not None


def test_delete_user_no_token_unauthorized(
        client: TestClient, db: SQLAlchemySession
):
    """
    Test attempt to delete a user without an authentication token.
    """
    user_to_delete = create_modifiable_test_user(db, suffix="DELNOTOKEN")
    user_roll_number_to_delete = user_to_delete.roll_number

    response = client.delete(
        f"{settings.API_V1_STR}/admin/users/{user_roll_number_to_delete}"
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    db_user_after_attempt = crud_user.get_user_by_roll_number(db, roll_number=user_roll_number_to_delete)
    assert db_user_after_attempt is not None
