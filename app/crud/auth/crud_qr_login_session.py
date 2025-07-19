from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models.auth.qr_login_session import QRLoginSession
from app.schemas.auth import qr_login_session


def create_qr_login_session(db: Session, *, obj_in: qr_login_session.QRLoginSessionCreate) -> QRLoginSession:
    db_obj = QRLoginSession(
        token=obj_in.token,
        status="pending"
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def get_qr_login_session_by_token(db: Session, *, token: str) -> QRLoginSession | None:
    return db.query(QRLoginSession).filter(QRLoginSession.token == token).first()


def update_qr_login_session(db: Session, *, db_obj: QRLoginSession, obj_in: qr_login_session.QRLoginSessionUpdate) -> QRLoginSession:
    if isinstance(obj_in, dict):
        update_data = obj_in
    else:
        update_data = obj_in.dict(exclude_unset=True)
    for field in update_data:
        setattr(db_obj, field, update_data[field])
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def cleanup_expired_sessions(db: Session):
    expiration_time = datetime.utcnow() - timedelta(minutes=5)
    db.query(QRLoginSession).filter(QRLoginSession.created_at < expiration_time).delete()
    db.commit()
