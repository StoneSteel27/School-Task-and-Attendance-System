from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError  # Import IntegrityError
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
    db_user_by_email = crud.crud_user.get_user_by_email(db, email=user_in.email)
    if db_user_by_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The user with this email already exists in the system.",
        )

    # Add pre-check for roll_number
    db_user_by_roll = crud.crud_user.get_user_by_roll_number(db, roll_number=user_in.roll_number)
    if db_user_by_roll:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"The user with roll number '{user_in.roll_number}' already exists in the system.",
        )

    hashed_password = get_password_hash(user_in.password)
    try:
        created_user = crud.crud_user.create_user(
            db=db,
            user_in=user_in,
            password_hash=hashed_password
        )
    except IntegrityError:  # Catch specific IntegrityError
        db.rollback()
        # This message is a fallback. The pre-checks for email and roll_number should catch most common cases.
        # This could be due to other unique constraints if any were added to the User model later.
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A database integrity error occurred. This could be due to a duplicate roll number or other unique data conflict not caught by pre-checks.",
        )
    except Exception as e:  # General catch-all
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred while creating the user: {str(e)}",
        )
    return created_user


# ... rest of the file (read_users, read_user_by_roll_number, etc.) remains the same
@router.get("/", response_model=List[schemas.User])
def read_users(
        db: Session = Depends(get_db),
        skip: int = 0,
        limit: int = 100,
        current_user: models.User = Depends(deps.get_current_active_superuser)
):
    users = crud.crud_user.get_users(db, skip=skip, limit=limit)
    return users


@router.get("/{user_roll_number}", response_model=schemas.User)
def read_user_by_roll_number(
        user_roll_number: str,
        db: Session = Depends(get_db),
        current_user: models.User = Depends(deps.get_current_active_superuser)
):
    db_user = crud.crud_user.get_user_by_roll_number(db, roll_number=user_roll_number)
    if db_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return db_user


@router.put("/{user_roll_number}", response_model=schemas.User)
def update_user_endpoint(
        user_roll_number: str,
        *,
        db: Session = Depends(get_db),
        user_in: schemas.UserUpdate,
        current_super_user: models.User = Depends(deps.get_current_active_superuser)
):
    db_user = crud.crud_user.get_user_by_roll_number(db, roll_number=user_roll_number)
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    new_hashed_password = None
    if user_in.password:
        new_hashed_password = get_password_hash(user_in.password)
        db_user.hashed_password = new_hashed_password

    # The crud_user.update_user needs to be robust against IntegrityError if roll_number or email is changed to an existing one
    try:
        updated_user = crud.crud_user.update_user(db=db, db_user=db_user, user_in=user_in)
    except IntegrityError:
        db.rollback()
        # Determine if it was email or roll_number. For simplicity, a generic message here.
        # More specific checks can be added in crud_user.update_user or here.
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Update failed. The new email or roll number may already be in use by another user.",
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred while updating the user: {str(e)}",
        )
    return updated_user


@router.delete("/{user_roll_number}", response_model=schemas.User)
def delete_user_endpoint(
        user_roll_number: str,
        db: Session = Depends(get_db),
        current_admin_user: models.User = Depends(deps.get_current_active_superuser)
):
    db_user_to_delete = crud.crud_user.get_user_by_roll_number(db, roll_number=user_roll_number)
    if not db_user_to_delete:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if db_user_to_delete.id == current_admin_user.id and current_admin_user.is_superuser:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Superuser cannot delete themselves.")

    deleted_user = crud.crud_user.remove_user(db=db, db_user_to_delete=db_user_to_delete)
    return deleted_user