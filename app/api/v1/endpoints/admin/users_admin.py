from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app import crud, models, schemas
from app.db.session import get_db
from app.core.security import get_password_hash
from app.api import deps

router = APIRouter()

@router.post("/", response_model=schemas.user.User, status_code=status.HTTP_201_CREATED)
def create_user_endpoint(
        *,
        db: Session = Depends(get_db),
        user_in: schemas.UserCreate,
        current_user: models.User = Depends(deps.get_current_active_superuser)
):
    """
    Create new user.
    Only accessible by superusers.
    """
    db_user = crud.crud_user.get_user_by_email(db, email=user_in.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The user with this email already exists in the system.",
        )

    hashed_password = get_password_hash(user_in.password)
    created_user = crud.crud_user.create_user(
        db=db,
        user_in=user_in,
        password_hash=hashed_password
    )
    return created_user

@router.get("/", response_model=List[schemas.User])  # Note: response_model is List[schemas.User]
def read_users(
        db: Session = Depends(get_db),
        skip: int = 0,
        limit: int = 100,
        current_user: models.User = Depends(deps.get_current_active_superuser)  # Protected
):
    """
    Retrieve all users.
    Accessible only by superusers.
    Supports pagination with skip and limit.
    """
    users = crud.crud_user.get_users(db, skip=skip, limit=limit)
    return users

@router.get("/{user_roll_number}", response_model=schemas.User)
def read_user_by_roll_number(
        user_roll_number: str,  # Path parameter is now user_roll_number (string)
        db: Session = Depends(get_db),
        current_user: models.User = Depends(deps.get_current_active_superuser)  # Still protected
):
    """
    Get a specific user by their roll number.
    Accessible only by superusers.
    """
    db_user = crud.crud_user.get_user_by_roll_number(db, roll_number=user_roll_number)
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return db_user

@router.put("/{user_roll_number}", response_model=schemas.User)
def update_user_endpoint(
        user_roll_number: str, # Path parameter is now user_roll_number (string)
        *,
        db: Session = Depends(get_db),
        user_in: schemas.UserUpdate,
        current_super_user: models.User = Depends(deps.get_current_active_superuser)
):
    """
    Update a user identified by their roll number.
    Accessible only by superusers.
    Superusers can update any user's details.
    """
    db_user = crud.crud_user.get_user_by_roll_number(db, roll_number=user_roll_number) # Fetch by roll_number
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Password handling: if user_in.password is provided, hash it and set it on db_user.
    # The crud.update_user function will then apply other updates from user_in,
    # excluding the plain password.
    new_hashed_password = None
    if user_in.password:
        new_hashed_password = get_password_hash(user_in.password)
        # Set the new hashed password directly on the ORM model instance
        db_user.hashed_password = new_hashed_password

    # The crud_user.update_user function will handle other field updates.
    # It's designed to ignore 'password' in user_in because hashing is done here.
    updated_user = crud.crud_user.update_user(db=db, db_user=db_user, user_in=user_in)
    return updated_user

@router.delete("/{user_roll_number}", response_model=schemas.User)
def delete_user_endpoint(
    user_roll_number: str, # Path parameter is now user_roll_number (string)
    db: Session = Depends(get_db),
    current_admin_user: models.User = Depends(deps.get_current_active_superuser) # Renamed for clarity
):
    """
    Delete a user identified by their roll number.
    Accessible only by superusers.
    """
    db_user_to_delete = crud.crud_user.get_user_by_roll_number(db, roll_number=user_roll_number) # Fetch by roll_number
    if not db_user_to_delete:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Optional: Prevent a superuser from deleting themselves
    if db_user_to_delete.id == current_admin_user.id and current_admin_user.is_superuser:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Superuser cannot delete themselves.")

    # Pass the fetched user object to the modified remove_user function
    deleted_user = crud.crud_user.remove_user(db=db, db_user_to_delete=db_user_to_delete)
    return deleted_user
