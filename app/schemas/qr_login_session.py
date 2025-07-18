from pydantic import BaseModel
from datetime import datetime


class QRLoginSessionBase(BaseModel):
    token: str
    status: str
    user_id: int | None = None


class QRLoginSessionCreate(BaseModel):
    token: str


class QRLoginSessionUpdate(BaseModel):
    status: str | None = None
    user_id: int | None = None


class QRLoginSessionInDBBase(QRLoginSessionBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True


class QRLoginSession(QRLoginSessionInDBBase):
    pass
