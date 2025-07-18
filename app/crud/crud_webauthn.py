from typing import Optional

from sqlalchemy.orm import Session

from app.models.webauthn import WebAuthnCredential, WebAuthnChallenge
from app.schemas.webauthn import WebAuthnCredentialCreate, WebAuthnCredentialUpdate


def get_credential_by_id(db: Session, credential_id: bytes) -> Optional[WebAuthnCredential]:
    return db.query(WebAuthnCredential).filter(WebAuthnCredential.credential_id == credential_id).first()


def get_credentials_by_user_id(db: Session, user_id: int) -> list[WebAuthnCredential]:
    return db.query(WebAuthnCredential).filter(WebAuthnCredential.user_id == user_id).all()


def create_credential(db: Session, obj_in: WebAuthnCredentialCreate) -> WebAuthnCredential:
    db_obj = WebAuthnCredential(
        user_id=obj_in.user_id,
        credential_id=obj_in.credential_id,
        public_key=obj_in.public_key,
        sign_count=obj_in.sign_count,
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def update_credential(db: Session, db_obj: WebAuthnCredential, obj_in: WebAuthnCredentialUpdate) -> WebAuthnCredential:
    if isinstance(obj_in, dict):
        update_data = obj_in
    else:
        update_data = obj_in.dict(exclude_unset=True)

    for field, value in update_data.items():
        setattr(db_obj, field, value)

    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def create_challenge(db: Session, challenge: str) -> WebAuthnChallenge:
    db_obj = WebAuthnChallenge(challenge=challenge)
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def get_challenge(db: Session, challenge: str) -> Optional[WebAuthnChallenge]:
    return db.query(WebAuthnChallenge).filter(WebAuthnChallenge.challenge == challenge).first()


def remove_challenge(db: Session, challenge: str):
    db_obj = db.query(WebAuthnChallenge).filter(WebAuthnChallenge.challenge == challenge).first()
    if db_obj:
        db.delete(db_obj)
        db.commit()
