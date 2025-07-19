from typing import Optional

from sqlalchemy.orm import Session

from app.models.auth.webauthn import WebAuthnCredential, WebAuthnChallenge
from app.schemas.auth.webauthn import WebAuthnCredentialCreate, WebAuthnCredentialUpdate


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


# Create a simple object to provide access to all WebAuthn CRUD functions
class CRUDWebAuthn:
    """CRUD operations for WebAuthn models"""

    def get_credential_by_id(self, db: Session, credential_id: bytes):
        return get_credential_by_id(db, credential_id)

    def get_credentials_by_user_id(self, db: Session, user_id: int):
        return get_credentials_by_user_id(db, user_id)

    def create_credential(self, db: Session, obj_in):
        return create_credential(db, obj_in)

    def update_credential(self, db: Session, db_obj, obj_in):
        return update_credential(db, db_obj, obj_in)

    def create_challenge(self, db: Session, challenge: str):
        return create_challenge(db, challenge)

    def get_challenge(self, db: Session, challenge: str):
        return get_challenge(db, challenge)

    def remove_challenge(self, db: Session, challenge: str):
        return remove_challenge(db, challenge)


# Create the instance that will be imported
webauthn = CRUDWebAuthn()
