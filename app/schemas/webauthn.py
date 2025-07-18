from pydantic import BaseModel, Field


class WebAuthnCredentialCreate(BaseModel):
    user_id: int
    credential_id: bytes
    public_key: bytes
    sign_count: int


class WebAuthnCredentialUpdate(BaseModel):
    sign_count: int


class WebAuthnCredential(WebAuthnCredentialCreate):
    id: int

    class Config:
        orm_mode = True


class WebAuthnRegistrationRequest(BaseModel):
    username: str = Field(..., description="The user's unique username or email.")
    display_name: str = Field(..., description="The user's display name.")

class WebAuthnRegistrationVerification(BaseModel):
    challenge: str
    credential: dict

class WebAuthnAuthenticationRequest(BaseModel):
    user_id: str

class WebAuthnAuthenticationVerification(BaseModel):
    challenge: str
    credential: dict

class WebAuthnRegistrationResponse(BaseModel):
    challenge: str
    options: dict
