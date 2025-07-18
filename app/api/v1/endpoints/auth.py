from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import json

from app.core.security import create_access_token, verify_password
from app.crud import crud_user
from app.schemas.token import Token
from app.db.session import get_db
from app.api import deps
from app.schemas import webauthn as webauthn_schema
from app import models
from attendance_system_tools.webauthn_handler import WebAuthnHandler

router = APIRouter()


@router.post("/login/access-token", response_model=Token)
def login_for_access_token(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
):
    """
    OAuth2 compatible token login, get an access token for future requests.
    'username' in form_data will be the user's email.
    """
    user = crud_user.get_user_by_email(db, email=form_data.username)

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")

    access_token = create_access_token(data={"sub": user.email})

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/register/webauthn/begin", response_model=webauthn_schema.WebAuthnRegistrationResponse)
def webauthn_registration_begin(
    *,
    registration_data: webauthn_schema.WebAuthnRegistrationRequest,
    current_user: models.User = Depends(deps.get_current_active_user),
    webauthn_handler: WebAuthnHandler = Depends(deps.get_webauthn_handler)
):
    """
    Begin WebAuthn registration by generating a challenge.
    """
    options_json = webauthn_handler.generate_registration_challenge(
        user_id=current_user.id,
        username=registration_data.username,
        user_display_name=registration_data.display_name
    )
    options = json.loads(options_json)
    challenge = options["challenge"]

    return {"challenge": challenge, "options": options}


@router.post("/register/webauthn/finish")
def webauthn_registration_finish(
    *,
    verification_data: webauthn_schema.WebAuthnRegistrationVerification,
    current_user: models.User = Depends(deps.get_current_active_user),
    webauthn_handler: WebAuthnHandler = Depends(deps.get_webauthn_handler)
):
    """
    Finish WebAuthn registration by verifying the client's response.
    """
    try:
        webauthn_handler.verify_registration_response(
            credential_creation_response_json=json.dumps(verification_data.credential),
            stored_challenge_hex=verification_data.challenge,
            user_id=current_user.id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    return {"status": "ok"}


@router.post("/login/webauthn/begin", response_model=webauthn_schema.WebAuthnRegistrationResponse)
def webauthn_authentication_begin(
    *,
    db: Session = Depends(get_db),
    authentication_data: webauthn_schema.WebAuthnAuthenticationRequest,
    webauthn_handler: WebAuthnHandler = Depends(deps.get_webauthn_handler)
):
    """
    Begin WebAuthn authentication by generating a challenge.
    """
    user = crud_user.get_user(db, user_id=int(authentication_data.user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    options_json = webauthn_handler.generate_authentication_challenge(
        user_id=user.id
    )
    options = json.loads(options_json)
    challenge = options["challenge"]

    return {"challenge": challenge, "options": options}


@router.post("/login/webauthn/finish", response_model=Token)
def webauthn_authentication_finish(
    *,
    db: Session = Depends(get_db),
    verification_data: webauthn_schema.WebAuthnAuthenticationVerification,
    webauthn_handler: WebAuthnHandler = Depends(deps.get_webauthn_handler)
):
    """
    Finish WebAuthn authentication by verifying the client's response.
    """
    try:
        user_handle = verification_data.credential["response"]["userHandle"]
        user = crud_user.get_user(db, user_id=int(user_handle))
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        verification = webauthn_handler.verify_authentication_response(
            authentication_response_json=json.dumps(verification_data.credential),
            stored_challenge_hex=verification_data.challenge,
            user_id=user.id
        )
    except (ValueError, KeyError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}
