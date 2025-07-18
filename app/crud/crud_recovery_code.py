from sqlalchemy.orm import Session
from app.models.recovery_code import RecoveryCode
from app.schemas.recovery_code import RecoveryCodeCreate, RecoveryCodeUpdate
from app.crud.base import CRUDBase

class CRUDRecoveryCode(CRUDBase[RecoveryCode, RecoveryCodeCreate, RecoveryCodeUpdate]):
    def get_by_hashed_code(self, db: Session, *, hashed_code: str) -> RecoveryCode | None:
        return db.query(RecoveryCode).filter(RecoveryCode.hashed_code == hashed_code).first()

recovery_code = CRUDRecoveryCode(RecoveryCode)
