from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app import crud, models, schemas
from app.db.session import get_db
from app.core.security import get_password_hash
from app.api import deps

router = APIRouter()


@router.get("/me", response_model=schemas.User)
def read_users_me(
        current_user: models.User = Depends(deps.get_current_active_user)  # Use get_current_active_user
):
    """
    Get current logged-in user's information.
    """
    return current_user