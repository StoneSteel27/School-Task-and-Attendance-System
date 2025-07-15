from datetime import date
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError

from app.models.announcement import Announcement # Import the Announcement model
from app.models.user import User # For relationships
from app.models.school_class import SchoolClass # For relationships
from app.schemas.announcement import AnnouncementCreate, AnnouncementUpdate # Import Pydantic schemas


def get_announcement(db: Session, announcement_id: int) -> Optional[Announcement]:
    """Retrieve a single announcement by its ID."""
    return (
        db.query(Announcement)
        .options(
            joinedload(Announcement.created_by_user),
            joinedload(Announcement.school_class)
        )
        .filter(Announcement.id == announcement_id)
        .first()
    )


def get_announcements(db: Session, skip: int = 0, limit: int = 100) -> List[Announcement]:
    """Retrieve all announcements, ordered by creation date."""
    return (
        db.query(Announcement)
        .options(
            joinedload(Announcement.created_by_user),
            joinedload(Announcement.school_class)
        )
        .order_by(Announcement.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_school_wide_announcements(db: Session, skip: int = 0, limit: int = 100) -> List[Announcement]:
    """Retrieve all school-wide announcements."""
    return (
        db.query(Announcement)
        .options(
            joinedload(Announcement.created_by_user)
        )
        .filter(Announcement.is_school_wide == True)
        .order_by(Announcement.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_class_announcements(db: Session, school_class_id: int, skip: int = 0, limit: int = 100) -> List[Announcement]:
    """Retrieve all announcements for a specific school class (not school-wide)."""
    return (
        db.query(Announcement)
        .options(
            joinedload(Announcement.created_by_user)
        )
        .filter(
            Announcement.school_class_id == school_class_id,
            Announcement.is_school_wide == False # Exclude school-wide announcements
        )
        .order_by(Announcement.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_subject_announcements_for_class(db: Session, school_class_id: int, subject: str, skip: int = 0, limit: int = 100) -> List[Announcement]:
    """Retrieve announcements for a specific subject within a school class."""
    return (
        db.query(Announcement)
        .options(
            joinedload(Announcement.created_by_user)
        )
        .filter(
            Announcement.school_class_id == school_class_id,
            Announcement.subject == subject,
            Announcement.is_school_wide == False
        )
        .order_by(Announcement.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_announcement(db: Session, *, announcement_in: AnnouncementCreate, created_by_user_id: int) -> Announcement:
    """Create a new announcement."""
    db_announcement = Announcement(
        **announcement_in.model_dump(),
        created_by_user_id=created_by_user_id
    )
    db.add(db_announcement)
    try:
        db.commit()
        db.refresh(db_announcement)
    except IntegrityError as e:
        db.rollback()
        raise IntegrityError(f"Database integrity error while creating announcement: {e.orig}", e.params, e.orig) from e
    except Exception as e:
        db.rollback()
        raise e
    return db_announcement


def update_announcement(db: Session, *, db_announcement: Announcement, announcement_in: AnnouncementUpdate) -> Announcement:
    """Update an existing announcement."""
    update_data = announcement_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_announcement, field, value)

    db.add(db_announcement)
    try:
        db.commit()
        db.refresh(db_announcement)
    except IntegrityError as e:
        db.rollback()
        raise IntegrityError(f"Database integrity error while updating announcement: {e.orig}", e.params, e.orig) from e
    except Exception as e:
        db.rollback()
        raise e
    return db_announcement


def delete_announcement(db: Session, *, announcement_id: int) -> Optional[Announcement]:
    """Delete an announcement by its ID."""
    db_announcement = db.query(Announcement).filter(Announcement.id == announcement_id).first()
    if db_announcement:
        db.delete(db_announcement)
        db.commit()
    return db_announcement
