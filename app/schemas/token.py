from pydantic import BaseModel
from typing import Optional


class Token(BaseModel):
    """
    Schema for the access token response after successful login.
    """
    access_token: str
    token_type: str


class TokenData(BaseModel):
    """
    Schema for the data embedded within the JWT token (the 'sub' claim primarily).
    This helps in validating the token's payload.
    """
    email: Optional[str] = None
