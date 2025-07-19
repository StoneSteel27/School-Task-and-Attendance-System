from sqlalchemy.orm import Session
from app.models.auth.recovery_code import RecoveryCode
from app.schemas.auth.recovery_code import RecoveryCodeCreate, RecoveryCodeLoginRequest

class CRUDRecoveryCode:
    def __init__(self, model):
        self.model = model

    def get_by_hashed_code(self, db: Session, *, hashed_code: str) -> RecoveryCode | None:
        return db.query(RecoveryCode).filter(RecoveryCode.hashed_code == hashed_code).first()

    def create(self, db: Session, *, obj_in: RecoveryCodeCreate) -> RecoveryCode:
        db_obj = self.model(**obj_in.model_dump())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, *, db_obj: RecoveryCode) -> RecoveryCode:
        db.delete(db_obj)
        db.commit()
        return db_obj

recovery_code = CRUDRecoveryCode(RecoveryCode)
