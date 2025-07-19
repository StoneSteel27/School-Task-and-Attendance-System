from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.api import deps
from app.db.session import get_db
from app import models, schemas, crud
from app.core.security import create_access_token
from app.schemas.auth.recovery_code import RecoveryCodesResponse, RecoveryCodeCreate, RecoveryCodeLoginRequest # ADDED THIS LINE
from app.schemas.auth.token import Token # ADDED THIS LINE

router = APIRouter()

@router.post("/recovery/generate", response_model=RecoveryCodesResponse)
def generate_recovery_codes(
    *,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """
    Generate a new set of recovery codes for the current user.
    This will invalidate all previously issued codes.
    """
    # 1. Invalidate all old codes for this user
    for old_code in current_user.recovery_codes:
        db.delete(old_code)
    
    # 2. Generate new plain-text codes
    plain_text_codes = deps.recovery_codes_manager.generate_recovery_codes()
    
    # 3. Hash and store the new codes
    for code in plain_text_codes:
        hashed_code = deps.recovery_codes_manager.get_code_hash(code)
        recovery_code_in = schemas.recovery_code.RecoveryCodeCreate(
            hashed_code=hashed_code,
            user_id=current_user.id
        )
        crud.recovery_code.create(db, obj_in=recovery_code_in)
        
    db.commit()
    
    # 4. Return the plain-text codes to the user to be saved
    return {"codes": plain_text_codes}

@router.post("/recovery/login", response_model=Token)
def recovery_login(
    *,
    db: Session = Depends(get_db),
    login_data: RecoveryCodeLoginRequest,
):
    """
    Log in using a one-time recovery code.
    """
    user = crud.crud_user.get_user_by_email(db, email=login_data.email)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    try:
        hashed_code_to_check = deps.recovery_codes_manager.get_code_hash(login_data.code)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid recovery code format.")

    recovery_code_obj = crud.recovery_code.get_by_hashed_code(db, hashed_code=hashed_code_to_check)

    if not recovery_code_obj or recovery_code_obj.user_id != user.id or recovery_code_obj.is_used:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or already used recovery code.")

    # Mark the code as used
    recovery_code_obj.is_used = True
    db.add(recovery_code_obj)
    db.commit()

    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}
