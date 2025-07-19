from pydantic import BaseModel, Field
from typing import List

class RecoveryCodeCreate(BaseModel):
    hashed_code: str = Field(..., description="The hashed recovery code.")
    user_id: int = Field(..., description="The ID of the user this recovery code belongs to.")

class RecoveryCodeLoginRequest(BaseModel):
    email: str = Field(..., description="The user's email address.")
    code: str = Field(..., description="The one-time recovery code.")

class RecoveryCodesResponse(BaseModel):
    codes: List[str]
