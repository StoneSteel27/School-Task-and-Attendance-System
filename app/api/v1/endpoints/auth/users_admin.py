from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List

from app import crud, models
from app.db.session import get_db
from app.core.security import get_password_hash
from app.api import deps
from app.schemas.auth.user import User as UserSchema, UserCreate, UserUpdate

router = APIRouter()


@router.post("/", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
def create_user_endpoint(
        *,
        db: Session = Depends(get_db),
        user_in: UserCreate,
        current_user: models.User = Depends(deps.get_current_active_superuser)
):
    """
    Create a new user.
    Accessible only by superusers.
    """
    # Check if a user with the same email or roll number already exists
    existing_user_email = crud.crud_user.get_user_by_email(db, email=user_in.email)
    if existing_user_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The user with this email already exists in the system.",
        )
    existing_user_roll = crud.crud_user.get_user_by_roll_number(db, roll_number=user_in.roll_number)
    if existing_user_roll:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The user with this roll number already exists in the system.",
        )

    password_hash = get_password_hash(user_in.password)
    try:
        user = crud.crud_user.create_user(db, user_in=user_in, password_hash=password_hash)
    except IntegrityError:  # Should be redundant due to checks above, but as a safeguard
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Database integrity error. The email or roll number may already exist."
        )
    return user


@router.get("/", response_model=List[UserSchema])
def read_users(
        db: Session = Depends(get_db),
        skip: int = 0,
        limit: int = 100,
        current_user: models.User = Depends(deps.get_current_active_superuser),
):
    """
    Retrieve users.
    """
    users = crud.crud_user.get_users(db, skip=skip, limit=limit)
    return users

@router.get("/{user_roll_number}", response_model=UserSchema)
def get_user_by_roll_number(
        *,
        db: Session = Depends(get_db),
        user_roll_number: str,
        current_user: models.User = Depends(deps.get_current_active_superuser),
):
    """
    Get a user by roll number.
    """
    user = crud.crud_user.get_user_by_roll_number(db, roll_number=user_roll_number)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    return user


@router.put("/{user_roll_number}", response_model=UserSchema)
def update_user_endpoint(
        *,
        db: Session = Depends(get_db),
        user_roll_number: str,
        user_in: UserUpdate,
        current_user: models.User = Depends(deps.get_current_active_superuser),
):
    """
    Update a user.
    """
    db_user = crud.crud_user.get_user_by_roll_number(db, roll_number=user_roll_number)
    if not db_user:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    # Check for duplicate email
    if user_in.email:
        existing_user = crud.crud_user.get_user_by_email(db, email=user_in.email)
        if existing_user and existing_user.id != db_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The user with this email already exists in the system.",
            )

    # Check for duplicate roll number
    if user_in.roll_number:
        existing_user = crud.crud_user.get_user_by_roll_number(db, roll_number=user_in.roll_number)
        if existing_user and existing_user.id != db_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The user with this roll number already exists in the system.",
            )

    # If password is being updated, hash it
    if user_in.password:
        hashed_password = get_password_hash(user_in.password)
        db_user.hashed_password = hashed_password

    user = crud.crud_user.update_user(db=db, db_user=db_user, user_in=user_in)
    return user


@router.delete("/{user_roll_number}", response_model=UserSchema)
def delete_user_endpoint(
        *,
        db: Session = Depends(get_db),
        user_roll_number: str,
        current_user: models.User = Depends(deps.get_current_active_superuser),
):
    """
    Delete a user.
    """
    user_to_delete = crud.crud_user.get_user_by_roll_number(db, roll_number=user_roll_number)
    if not user_to_delete:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    # Superusers cannot delete their own account
    if current_user.id == user_to_delete.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Superusers cannot delete their own account.",
        )

    deleted_user = crud.crud_user.remove_user(db=db, db_user_to_delete=user_to_delete)
    return deleted_user