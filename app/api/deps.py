from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from sqlalchemy.orm import Session
from jose import JWTError

from app.core.config import settings
from app.core.security import decode_token
from app.db.session import get_db
from app.models.user import User as UserModel
from app.crud import crud_user
from app.schemas.token import TokenData

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login/access-token"
)


async def get_current_user(
        db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> UserModel:
    """
    Dependency to get the current user from the token.
    1. Gets token from Authorization header (via oauth2_scheme).
    2. Decodes token using our security utility.
    3. Fetches user from DB based on token data.
    """
    token_data = decode_token(token)  # This will raise HTTPException if token is invalid

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
