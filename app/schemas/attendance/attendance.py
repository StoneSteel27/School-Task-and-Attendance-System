from pydantic import BaseModel, Field

class AttendanceRequest(BaseModel):
    latitude: float = Field(..., description="The user's current latitude.")
    longitude: float = Field(..., description="The user's current longitude.")
