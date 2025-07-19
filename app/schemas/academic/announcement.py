from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

# --- Base Schemas ---
class AnnouncementBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Title of the announcement.")
    content: str = Field(..., description="Full content of the announcement.")
    attachment_url: Optional[str] = Field(None, description="URL to an optional attachment for the announcement.")
    is_school_wide: bool = Field(False, description="True if this announcement is for the entire school, False for class/subject specific.")
    # school_class_id and subject are optional and depend on is_school_wide
    school_class_id: Optional[int] = Field(None, description="ID of the school class this announcement is for. Null if school-wide.")
    subject: Optional[str] = Field(None, max_length=100, description="The subject this announcement belongs to. Null if school-wide or class-wide.")


# --- Create Schemas ---
class AnnouncementCreate(AnnouncementBase):
    # created_by_user_id will be derived from authentication context
    pass


# --- Update Schemas ---
class AnnouncementUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255, description="New title of the announcement.")
    content: Optional[str] = Field(None, description="New full content of the announcement.")
    attachment_url: Optional[str] = Field(None, description="New URL to an optional attachment.")
    is_school_wide: Optional[bool] = Field(None, description="New school-wide status.")
    school_class_id: Optional[int] = Field(None, description="New school class ID.")
    subject: Optional[str] = Field(None, max_length=100, description="New subject.")


# --- Full Announcement Schema (for responses) ---
class Announcement(AnnouncementBase):
    id: int = Field(..., description="Unique ID of the announcement.")
    created_by_user_id: Optional[int] = Field(None, description="ID of the user who created the announcement.")
    created_at: datetime = Field(..., description="Timestamp when the announcement was created.")

    # Nested relationships (optional)
    # from .user import User as UserSchema
    # created_by_user: Optional[UserSchema] = None
    # from .school_class import SchoolClassBase as SchoolClassSchema
    # school_class: Optional[SchoolClassSchema] = None

    model_config = ConfigDict(from_attributes=True)
