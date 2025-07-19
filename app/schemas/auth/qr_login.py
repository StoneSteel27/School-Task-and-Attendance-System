from pydantic import BaseModel, Field

class QRLoginApproveRequest(BaseModel):
    token: str = Field(..., description="The temporary token scanned from the QR code.")

class QRLoginPollResponse(BaseModel):
    status: str # e.g., "pending", "approved", "expired"
    access_token: str | None = None
    token_type: str | None = "bearer"
