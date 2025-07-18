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
from app.models.user import User as UserModel
from app.schemas.user import UserCreate
from app.core.security import get_password_hash
from app.crud import crud_user

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
def test_normal_user(db: SQLAlchemySession) -> UserModel: # Use the overridden db fixture
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
    else: # Ensure existing user is normal user and active
        user.is_superuser = False
        user.is_active = True
        user.role = "student"
        # user.hashed_password = get_password_hash(password) # If password reset needed
        db.add(user)
        db.commit()
        db.refresh(user)
    return user

# --- Token Fixtures ---
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