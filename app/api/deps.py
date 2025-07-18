from fastapi import Depends, HTTPException, status, Path  # Add Path
from fastapi.security import OAuth2PasswordBearer

from sqlalchemy.orm import Session
from jose import JWTError

from app.core.config import settings
from app.core.security import decode_token
from app.db.session import get_db
from app.models.user import User as UserModel  # Keep existing alias
from app.crud import crud_user  # Ensure crud_user is imported
from app.schemas.token import TokenData

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login/access-token"
)


async def get_current_user(
        db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> UserModel:
    """
    Dependency to get the current user from the token.
    """
    token_data = decode_token(token)
    user = crud_user.get_user_by_email(db, email=token_data.email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


async def get_current_active_user(
        current_user: UserModel = Depends(get_current_user)
) -> UserModel:
    """
    Dependency that builds on get_current_user to ensure the user is active.
    """
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return current_user


async def get_current_active_superuser(
        current_user: UserModel = Depends(get_current_active_user)
) -> UserModel:
    """
    Dependency that builds on get_current_active_user to ensure the user is a superuser.
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges (not a superuser)"
        )
    return current_user


# --- NEW PERMISSION DEPENDENCIES ---

async def get_student_for_view_permission(
        student_roll_number: str = Path(..., description="The roll number of the student to retrieve."),
        # Use Path to get from URL
        db: Session = Depends(get_db),
        current_user: UserModel = Depends(get_current_active_user)
) -> UserModel:
    """
    Dependency to get a student by roll number and check view permissions.
    Allows access if the current user is the student themselves or a superuser.
    Returns the student ORM object if authorized.
    """
    target_student = crud_user.get_user_by_roll_number(db, roll_number=student_roll_number)
    if not target_student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with roll number '{student_roll_number}' not found."
        )

    # It's good practice to also verify the role here if the endpoint is specifically for 'students'
    if target_student.role != "student":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            # Or 404 if you want to hide that a user exists but isn't a student
            detail=f"User with roll number '{student_roll_number}' is not a student."
        )

    if not (current_user.is_superuser or current_user.id == target_student.id):
        print(f"current_user.id: {current_user.id}, target_student.id: {target_student.id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this student's data."
        )
    return target_student


async def get_teacher_for_view_permission(
        teacher_roll_number: str = Path(..., description="The roll number of the teacher to retrieve."),  # Use Path
        db: Session = Depends(get_db),
        current_user: UserModel = Depends(get_current_active_user)
) -> UserModel:
    """
    Dependency to get a teacher by roll number and check view permissions.
    Allows access if the current user is the teacher themselves or a superuser.
    Returns the teacher ORM object if authorized.
    """
    target_teacher = crud_user.get_user_by_roll_number(db, roll_number=teacher_roll_number)
    if not target_teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Teacher with roll number '{teacher_roll_number}' not found."
        )

    if target_teacher.role != "teacher":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,  # Or 404
            detail=f"User with roll number '{teacher_roll_number}' is not a teacher."
        )

    if not (current_user.is_superuser or current_user.id == target_teacher.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this teacher's data."
        )
    return target_teacher


# --- Tool Managers ---

from attendance_system_tools.webauthn_handler import WebAuthnHandler
from attendance_system_tools.qr_code_manager import QRCodeManager
from attendance_system_tools.recovery_codes_manager import RecoveryCodesManager
from attendance_system_tools.geofence_manager import GeofenceManager

# WebAuthn
def get_webauthn_handler(db: Session = Depends(get_db)) -> WebAuthnHandler:
    return WebAuthnHandler(
        rp_id="localhost",  # For local development
        rp_name="School Attendance System",
        rp_origin="http://localhost:3000",  # Assuming a React frontend running on 3000
        db=db
    )

# QR Code
qr_code_manager = QRCodeManager()

# Recovery Codes
recovery_codes_manager = RecoveryCodesManager()

# Geofence
geofence_manager = GeofenceManager()

# --- Geofence Configuration Loading ---
import json
from pathlib import Path

def load_geofence_config():
    # Assuming deps.py is in app/api/, the project root is 3 levels up.
    config_path = Path(__file__).resolve().parent.parent.parent / "geofence_config.json"
    try:
        with open(config_path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"WARNING: Geofence configuration file not found at {config_path}. Geofencing will not work.")
        return []
    except json.JSONDecodeError:
        print(f"ERROR: Could not decode {config_path}. Geofencing will not work.")
        return []

# Load the geofences once on startup
SCHOOL_GEOFENCES = load_geofence_config()


