import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event as sqlalchemy_event  # Add sqlalchemy_event
from sqlalchemy.orm import sessionmaker, Session as SQLAlchemySession
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.config import settings
from app.db.base_class import Base
from app.db.session import get_db, \
    SessionLocal as AppSessionLocal  # Import AppSessionLocal if TestingSessionLocal is based on it
from app.models.auth.user import User as UserModel
from app.schemas.auth.user import UserCreate
from app.core.security import get_password_hash
from app.crud.auth import crud_user
from app.models.core.school_class import SchoolClass, teacher_class_association


# --- Test Database Setup ---
SQLALCHEMY_DATABASE_URL_TEST = "sqlite:///:memory:"
engine_test = create_engine(
    SQLALCHEMY_DATABASE_URL_TEST,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
# Use the same sessionmaker factory as your app if possible, or ensure compatibility
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    Base.metadata.create_all(bind=engine_test)
    yield
    # Base.metadata.drop_all(bind=engine_test) # Optional for :memory:


@pytest.fixture(scope="function")
def db() -> SQLAlchemySession:
    connection = engine_test.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    # Begin a nested transaction (using SAVEPOINT)
    nested = session.begin_nested()

    @sqlalchemy_event.listens_for(session, "after_transaction_end")
    def end_savepoint(sess, trans):
        nonlocal nested
        if not nested.is_active:
            nested = session.begin_nested()

    app.dependency_overrides[get_db] = lambda: session

    yield session

    # Rollback the overall transaction, undoing everything
    app.dependency_overrides.clear()
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db: SQLAlchemySession) -> TestClient:
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

# --- User Fixtures ---
@pytest.fixture(scope="function")
def test_superuser(db: SQLAlchemySession) -> UserModel: # Use the overridden db fixture
    email = settings.FIRST_SUPERUSER_EMAIL or "testadmin@example.com"
    password = settings.FIRST_SUPERUSER_PASSWORD or "testadminpass"
    roll_number = settings.FIRST_SUPERUSER_ROLL_NUMBER or "TEST_ADMIN_001"
    full_name = settings.FIRST_SUPERUSER_FULL_NAME or "Test Admin User"

    user = crud_user.get_user_by_email(db, email=email)
    if not user:
        user_in_create = UserCreate(
            email=email,
            password=password,
            full_name=full_name,
            roll_number=roll_number,
            is_superuser=True,
            is_active=True,
            role="admin"
        )
        hashed_password = get_password_hash(password)
        user = crud_user.create_user(db=db, user_in=user_in_create, password_hash=hashed_password)
    else: # Ensure existing user is superuser and active for test consistency
        user.is_superuser = True
        user.is_active = True
        user.role = "admin" # Ensure role is correct
        # If password needs to be reset for tests:
        # user.hashed_password = get_password_hash(password)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user

@pytest.fixture(scope="function")
def test_teacher(db: SQLAlchemySession) -> UserModel:
    email = "testteacher1@example.com"  # Changed email to avoid conflict
    password = "testteacherpass"
    roll_number = "TEST_TEACHER_001"
    full_name = "Test Teacher User"

    user = crud_user.get_user_by_email(db, email=email)
    if not user:
        user_in_create = UserCreate(
            email=email,
            password=password,
            full_name=full_name,
            roll_number=roll_number,
            is_superuser=False,
            is_active=True,
            role="teacher"
        )
        hashed_password = get_password_hash(password)
        user = crud_user.create_user(db=db, user_in=user_in_create, password_hash=hashed_password)
    else:
        user.is_superuser = False
        user.is_active = True
        user.role = "teacher"
        db.add(user)
        db.commit()
        db.refresh(user)
    return user

@pytest.fixture(scope="function")
def test_teacher_user(db: SQLAlchemySession) -> UserModel:
    """
    Creates a teacher user for testing purposes.
    """
    email = "testteacher@example.com"
    password = "testpassword"
    user = crud_user.get_user_by_email(db, email=email)
    if not user:
        user_in = UserCreate(
            email=email,
            password=password,
            role="teacher",
            full_name="Test Teacher",
            roll_number="T123"
        )
        user = crud_user.create_user(db, user_in=user_in, password_hash=get_password_hash(password))
        # Explicitly commit and flush to ensure the user is in the database
        db.commit()
        db.flush()
    else:
        # Always update password and role for test reliability
        user.hashed_password = get_password_hash(password)
        user.role = "teacher"
        user.is_active = True
        user.is_superuser = False
        db.add(user)
        db.commit()
        db.flush()
        db.refresh(user)
    return user

@pytest.fixture(scope="function")
def test_normal_user(db: SQLAlchemySession, test_teacher: UserModel) -> UserModel: # Use the overridden db fixture
    # Create a class
    school_class = SchoolClass(class_code="C-101", name="Test Class", grade="10", section="A")
    db.add(school_class)
    db.commit()
    db.refresh(school_class)

    # Associate teacher with subjects for the class
    db.execute(teacher_class_association.insert().values(teacher_id=test_teacher.id, class_id=school_class.id, subject="Math"))
    db.execute(teacher_class_association.insert().values(teacher_id=test_teacher.id, class_id=school_class.id, subject="Science"))
    db.commit()


    email = "testuser@example.com"
    password = "testuserpass"
    roll_number = "TEST_USER_001"
    full_name = "Test Normal User"

    user = crud_user.get_user_by_email(db, email=email)
    if not user:
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

    user.school_class_id = school_class.id
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

# --- Token Fixtures ---
def get_auth_headers(client: TestClient, email: str, password: str) -> dict[str, str]:
    login_data = {"username": email, "password": password}
    r = client.post(f"{settings.API_V1_STR}/auth/login/access-token", data=login_data)
    tokens = r.json()
    if "access_token" not in tokens:
        raise Exception(f"Login failed for {email}. Response: {tokens}")
    return {"Authorization": f"Bearer {tokens['access_token']}"}

@pytest.fixture(scope="function")
def superuser_token_headers(client: TestClient, test_superuser: UserModel) -> dict[str, str]:
    # Note: test_superuser fixture ensures the user exists in the DB tied to the 'client's session override
    login_data = {
        "username": test_superuser.email,
        "password": settings.FIRST_SUPERUSER_PASSWORD or "testadminpass", # Must match password in test_superuser
    }
    r = client.post(f"{settings.API_V1_STR}/auth/login/access-token", data=login_data)
    response_json = r.json()
    assert r.status_code == 200, f"Failed to log in superuser for token generation: {response_json}"
    token = response_json["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture(scope="function")
def normal_user_token_headers(client: TestClient, test_normal_user: UserModel) -> dict[str, str]:
    login_data = {
        "username": test_normal_user.email,
        "password": "testuserpass", # Must match password in test_normal_user
    }
    r = client.post(f"{settings.API_V1_STR}/auth/login/access-token", data=login_data)
    response_json = r.json()
    assert r.status_code == 200, f"Failed to log in normal user for token generation: {response_json}"
    token = response_json["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture(scope="function")
def teacher_token_headers(client: TestClient, test_teacher_user: UserModel) -> dict[str, str]:
    """
    Returns authentication headers for a teacher user.
    """
    return get_auth_headers(client, test_teacher_user.email, "testpassword")

@pytest.fixture(scope="function")
def test_teacher_direct_fixture(db: SQLAlchemySession, test_teacher_user: UserModel) -> dict[str, str]:
    """
    Creates a teacher user for testing purposes and returns the auth headers directly.
    This is a more direct approach that bypasses the need for separate login.
    """
    from app.core.security import create_access_token
    from datetime import timedelta
    from app.core.config import settings

    # Create a token directly without going through the login endpoint
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": test_teacher_user.email}, expires_delta=access_token_expires
    )

    # Return the auth headers
    return {"Authorization": f"Bearer {access_token}"}
