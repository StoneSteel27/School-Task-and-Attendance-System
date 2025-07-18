from pydantic import BaseModel, Field

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
