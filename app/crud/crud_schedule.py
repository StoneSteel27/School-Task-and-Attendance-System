from datetime import date
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError

from app.models.schedule import ClassScheduleSlot, Holiday  # DB Models
from app.schemas.schedule import (  # Pydantic Schemas
    ClassScheduleSlotCreateInput,
    HolidayCreate, HolidayUpdate
)


# --- ClassScheduleSlot CRUD (Assumed to be correct from previous step) ---

def replace_schedule_for_class(
        db: Session, *, school_class_id: int, new_slots_data: List[ClassScheduleSlotCreateInput]
) -> List[ClassScheduleSlot]:
    """
    Replaces the entire schedule for a given class.
    Deletes all existing schedule slots for the class and creates new ones.
    """
    db.query(ClassScheduleSlot).filter(ClassScheduleSlot.school_class_id == school_class_id).delete(
        synchronize_session=False)

    created_slots_orm: List[ClassScheduleSlot] = []
    for slot_data in new_slots_data:
        db_slot = ClassScheduleSlot(
            **slot_data.model_dump(),
            school_class_id=school_class_id
        )
        db.add(db_slot)
        created_slots_orm.append(db_slot)

    try:
        db.commit()
        for slot_orm_instance in created_slots_orm:
            db.refresh(slot_orm_instance)
    except IntegrityError as e:
        db.rollback()
        raise IntegrityError(f"Integrity error during schedule replacement: {e.orig}", e.params, e.orig) from e
    except Exception as e:
        db.rollback()
        raise e

    return created_slots_orm


def get_schedule_slots_for_class(db: Session, school_class_id: int) -> List[ClassScheduleSlot]:
    """Retrieves all schedule slots for a given class, ordered by day and period."""
    return (
        db.query(ClassScheduleSlot)
        .filter(ClassScheduleSlot.school_class_id == school_class_id)
        .order_by(ClassScheduleSlot.day_of_week, ClassScheduleSlot.period_number)
        .all()
    )


def get_schedule_slots_for_teacher(
        db: Session, teacher_id: int, day_of_week: Optional[int] = None
) -> List[ClassScheduleSlot]:
    """Retrieves schedule slots for a given teacher, optionally filtered by day of the week."""
    query = db.query(ClassScheduleSlot).filter(ClassScheduleSlot.teacher_id == teacher_id)
    if day_of_week is not None:
        query = query.filter(ClassScheduleSlot.day_of_week == day_of_week)
    return query.order_by(ClassScheduleSlot.day_of_week, ClassScheduleSlot.period_number).all()


def get_schedule_slot_by_id(db: Session, slot_id: int) -> Optional[ClassScheduleSlot]:
    """Retrieves a single schedule slot by its ID."""
    return db.query(ClassScheduleSlot).filter(ClassScheduleSlot.id == slot_id).first()


# --- Holiday CRUD (Revised for Date Ranges) ---

def create_holiday(db: Session, *, holiday_in: HolidayCreate) -> Holiday:
    """
    Creates a single holiday period.
    Pydantic schema HolidayCreate should have validated start_date <= end_date.
    """
    # Application-level check for overlapping holiday periods could be added here if needed,
    # though it can be complex to do efficiently for all grade_filter combinations.
    db_holiday = Holiday(**holiday_in.model_dump())
    db.add(db_holiday)
    try:
        db.commit()
        db.refresh(db_holiday)
    except IntegrityError as e:  # Catch other potential DB integrity issues
        db.rollback()
        raise IntegrityError(f"Database integrity error while creating holiday: {e.orig}", e.params, e.orig) from e
    return db_holiday


def bulk_create_holidays(db: Session, *, holidays_in: List[HolidayCreate]) -> List[Holiday]:
    """
    Creates multiple holiday periods in a single transaction.
    If any holiday causes an error, the entire batch is rolled back.
    Pydantic schemas should have validated start_date <= end_date for each item.
    """
    # More advanced overlap checking for the whole batch could be done here before adding to session.
    created_holidays_orm: List[Holiday] = []
    for holiday_data in holidays_in:
        db_holiday = Holiday(**holiday_data.model_dump())
        db.add(db_holiday)
        created_holidays_orm.append(db_holiday)

    try:
        db.commit()
        for holiday_obj in created_holidays_orm:
            db.refresh(holiday_obj)
    except IntegrityError as e:
        db.rollback()
        raise IntegrityError(f"Batch holiday creation failed due to a database integrity issue: {e.orig}", e.params,
                             e.orig) from e
    except Exception as e:
        db.rollback()
        raise e
    return created_holidays_orm


def get_holiday_by_id(db: Session, holiday_id: int) -> Optional[Holiday]:
    """Retrieves a holiday period by its ID."""
    return db.query(Holiday).filter(Holiday.id == holiday_id).first()


def get_holidays_active_on_date(
        db: Session, *, target_date: date, grade_filter_value: Optional[str] = None
) -> List[Holiday]:
    """
    Retrieves all holiday periods that are active on a specific target_date,
    optionally filtered by grade.
    """
    query = db.query(Holiday).filter(
        Holiday.start_date <= target_date,
        Holiday.end_date >= target_date
    )

    if grade_filter_value is not None:
        query = query.filter(
            (Holiday.grade_filter == grade_filter_value) | (Holiday.grade_filter.is_(None))
        )
    return query.order_by(Holiday.start_date).all()


def get_holidays(
        db: Session, *, skip: int = 0, limit: int = 100,
        query_start_date: Optional[date] = None,
        query_end_date: Optional[date] = None,
        grade_filter_value: Optional[str] = None
) -> List[Holiday]:
    """
    Retrieves a list of holiday periods, with optional pagination and filtering.
    - query_start_date, query_end_date: Finds holidays overlapping this range.
    - grade_filter_value: Filters for a specific grade or all (if grade_filter_value is None and not explicitly "all").
    """
    query = db.query(Holiday)

    # Filter for holidays overlapping with the query_start_date and query_end_date range
    if query_start_date and query_end_date:
        query = query.filter(
            Holiday.start_date <= query_end_date,  # Holiday starts before or on query range end
            Holiday.end_date >= query_start_date  # Holiday ends after or on query range start
        )
    elif query_start_date:  # Find holidays that are active on or after query_start_date
        query = query.filter(Holiday.end_date >= query_start_date)
    elif query_end_date:  # Find holidays that are active on or before query_end_date
        query = query.filter(Holiday.start_date <= query_end_date)

    if grade_filter_value is not None:
        query = query.filter(
            (Holiday.grade_filter == grade_filter_value) | (Holiday.grade_filter.is_(None))
        )

    return query.order_by(Holiday.start_date).offset(skip).limit(limit).all()


def update_holiday(db: Session, *, db_holiday: Holiday, holiday_in: HolidayUpdate) -> Holiday:
    """
    Updates an existing holiday period.
    Pydantic schema HolidayUpdate should validate date order if both start/end are provided.
    """
    update_data = holiday_in.model_dump(exclude_unset=True)

    # More robust date validation if only one date is changed:
    # temp_start_date = update_data.get('start_date', db_holiday.start_date)
    # temp_end_date = update_data.get('end_date', db_holiday.end_date)
    # if temp_end_date < temp_start_date:
    #     raise ValueError("Update results in end_date being before start_date")

    for field, value in update_data.items():
        setattr(db_holiday, field, value)
    db.add(db_holiday)
    try:
        db.commit()
        db.refresh(db_holiday)
    except IntegrityError as e:
        db.rollback()
        raise IntegrityError(f"Database integrity error while updating holiday: {e.orig}", e.params, e.orig) from e
    return db_holiday


def delete_holiday(db: Session, *, holiday_id: int) -> Optional[Holiday]:
    """Deletes a holiday period by its ID. Returns the deleted object or None if not found."""
    db_holiday = db.query(Holiday).filter(Holiday.id == holiday_id).first()
    if db_holiday:
        db.delete(db_holiday)
        db.commit()
    return db_holiday

def get_schedule_slots_for_teacher(
    db: Session, teacher_id: int, day_of_week: Optional[int] = None
) -> List[ClassScheduleSlot]:
    """Retrieves schedule slots for a given teacher, optionally filtered by day of the week.
    Eagerly loads the associated school_class for each slot."""
    query = db.query(ClassScheduleSlot).filter(ClassScheduleSlot.teacher_id == teacher_id)
    # Eager load the school_class to access its grade without N+1 queries later
    query = query.options(joinedload(ClassScheduleSlot.school_class))
    if day_of_week is not None:
        query = query.filter(ClassScheduleSlot.day_of_week == day_of_week)
    return query.order_by(ClassScheduleSlot.day_of_week, ClassScheduleSlot.period_number).all()