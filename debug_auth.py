"""
Debug script for authentication issues
"""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from app.db.base_class import Base
from app.db.session import get_db
from app.main import app
from app.core.security import get_password_hash
from app.models.auth.user import User
from app.schemas.auth.user import UserCreate
from app.crud.auth import crud_user

# Use a persistent SQLite file instead of in-memory for debugging
SQLALCHEMY_DATABASE_URL_TEST = "sqlite:///./test_debug.db"
engine_test = create_engine(
    SQLALCHEMY_DATABASE_URL_TEST,
    connect_args={"check_same_thread": False},
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)

# Create all tables
Base.metadata.drop_all(bind=engine_test)  # Start fresh
Base.metadata.create_all(bind=engine_test)

# Create a session
db = TestingSessionLocal()

# Override the get_db dependency
app.dependency_overrides[get_db] = lambda: db

# Create a test client
client = TestClient(app)

# Create a test teacher user
email = "testteacher@example.com"
password = "testpassword"

user = crud_user.get_user_by_email(db, email=email)
if not user:
    user_in = UserCreate(
        email=email,
        password=password,
        role="teacher",
        full_name="Test Teacher",
        roll_number="T123",
        is_active=True
    )
    # Create the user directly
    hashed_password = get_password_hash(password)
    user = User(
        email=email,
        hashed_password=hashed_password,
        role="teacher",
        full_name="Test Teacher",
        roll_number="T123",
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    print(f"Created new user with ID: {user.id}")
else:
    # Update existing user
    user.hashed_password = get_password_hash(password)
    user.role = "teacher"
    user.is_active = True
    db.add(user)
    db.commit()
    db.refresh(user)
    print(f"Updated existing user with ID: {user.id}")

# Try to login
from app.core.config import settings
login_data = {"username": email, "password": password}
response = client.post(f"{settings.API_V1_STR}/auth/login/access-token", data=login_data)
print(f"Login response status: {response.status_code}")
print(f"Login response body: {response.json()}")

# Clean up
db.close()
