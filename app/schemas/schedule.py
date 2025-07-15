from datetime import date
from typing import List, Optional
from pydantic import BaseModel, Field, conint, model_validator, ConfigDict  # Add model_validator for Pydantic v2+


# If you decide to embed full teacher details in schedule responses:
# from .user import User as UserSchema # Ensure UserSchema is defined appropriately

# --- Schedule Schemas ---

class ClassScheduleSlotBase(BaseModel):
    """Base schema for a class schedule slot, used for creation and reading."""
    subject_name: str = Field(..., description="Name of the subject for this slot, e.g., Mathematics.", min_length=1,
                              max_length=100)
    day_of_week: conint(ge=0, le=6) = Field(..., description="Day of the week (0=Monday, 1=Tuesday, ..., 6=Sunday).")
    period_number: conint(gt=0) = Field(..., description="Period number in the day (e.g., 1, 2, 3...).")
    teacher_id: Optional[int] = Field(None,
                                      description="ID of the teacher assigned to this slot. Nullable if unassigned.")
    # school_class_id is intentionally omitted here for payload schemas that are nested under a class path.
    # It will be part of the database model and the full response schema.


class ClassScheduleSlotCreateInput(ClassScheduleSlotBase):
    """
    Schema for creating a single schedule slot.
    school_class_id will be added by the CRUD function based on the API path context.
    """
    # No school_class_id here, as it's contextual from the class whose schedule is being defined.
    pass


class ClassScheduleSlotsBulkCreate(BaseModel):
    """Payload for creating or replacing the entire schedule for a class."""
    slots: List[ClassScheduleSlotCreateInput] = Field(...,
                                                      description="List of schedule slots for the class. This will typically replace the existing schedule.")


class ClassScheduleSlotUpdate(BaseModel):
    """Schema for updating an existing schedule slot (e.g., changing teacher or subject)."""
    subject_name: Optional[str] = Field(None, description="New name of the subject.", min_length=1, max_length=100)
    day_of_week: Optional[conint(ge=0, le=6)] = Field(None, description="New day of the week.")
    period_number: Optional[conint(gt=0)] = Field(None, description="New period number.")
    teacher_id: Optional[int] = Field(None, description="New ID of the teacher. Set to null to unassign.")
    # school_class_id is not updatable; move slot by deleting and creating in new class.


class ClassScheduleSlot(ClassScheduleSlotBase):  # Full response schema for a slot
    id: int = Field(..., description="Unique ID of the schedule slot.")
    school_class_id: int = Field(..., description="ID of the school class this slot belongs to.")

    # If you want to include full teacher details:
    # teacher: Optional[UserSchema] = None

    model_config = ConfigDict(from_attributes=True)  # Use model_config


# --- Holiday Schemas ---

class HolidayBase(BaseModel):
    """Base schema for a holiday, now supporting date ranges."""
    start_date: date = Field(..., description="The start date of the holiday period.")
    end_date: date = Field(..., description="The end date of the holiday period.")
    description: str = Field(..., description="Description of the holiday (e.g., Summer Break, National Day).",
                             min_length=1, max_length=255)
    grade_filter: Optional[str] = Field(None,
                                        description="Grade(s) this holiday applies to. Null for all grades. E.g., '5', '9-12', 'All'.",
                                        max_length=100)

    @model_validator(mode='after')
    def check_dates_order(cls, values):
        start, end = values.start_date, values.end_date
        if start and end and end < start:
            raise ValueError("end_date cannot be before start_date")
        return values


class HolidayCreate(HolidayBase):
    """Schema for creating a new holiday period."""
    pass


class HolidayUpdate(BaseModel):
    """
    Schema for updating an existing holiday. All fields are optional.
    If start_date or end_date is provided, they should be validated together.
    """
    start_date: Optional[date] = Field(None, description="New start date for the holiday period.")
    end_date: Optional[date] = Field(None, description="New end date for the holiday period.")
    description: Optional[str] = Field(None, description="New description.", min_length=1, max_length=255)
    grade_filter: Optional[str] = Field(None, description="New grade filter.", max_length=100)

    @model_validator(mode='after')
    def check_update_dates_order(cls, values):
        start, end = values.start_date, values.end_date
        if start and end and end < start:
            raise ValueError("end_date cannot be before start_date if both are updated")

        return values


class Holiday(HolidayBase):  # Full response schema for a holiday period
    id: int = Field(..., description="Unique ID of the holiday period.")

    model_config = ConfigDict(from_attributes=True)  # Use model_config


class HolidayBulkCreate(BaseModel):
    """Payload for creating multiple holiday periods at once."""
    holidays: List[HolidayCreate] = Field(..., description="A list of holiday periods to create.")