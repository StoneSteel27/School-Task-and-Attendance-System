from fastapi import APIRouter, Depends, HTTPException, status, Path, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app import crud, models, schemas
from app.api import deps
from app.db.session import get_db

router = APIRouter()

# --- Admin Announcement Endpoints ---

@router.post(
    "/",
    response_model=schemas.Announcement,
    status_code=status.HTTP_201_CREATED,
    summary="Admin: Create a new announcement (school-wide, class-specific, or subject-specific)"
)
def create_announcement_by_admin(
    announcement_in: schemas.AnnouncementCreate,
    db: Session = Depends(get_db),
    current_superuser: models.User = Depends(deps.get_current_active_superuser)
):
    """
    Allows a superuser to create a new announcement. 
    Announcements can be school-wide, class-specific, or subject-specific within a class.
    """
    if announcement_in.school_class_id:
        db_class = crud.crud_school_class.get_school_class_orm_by_id(db, class_id=announcement_in.school_class_id)
        if not db_class:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Class with ID '{announcement_in.school_class_id}' not found.")
        
        # If it's class-specific or subject-specific, ensure is_school_wide is False
        if announcement_in.is_school_wide:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot set school_class_id for a school-wide announcement.")

    elif announcement_in.subject:
        # If subject is provided without school_class_id, it's ambiguous or invalid for non-school-wide.
        # School-wide announcements don't have a subject.
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Subject cannot be specified without a school_class_id for non-school-wide announcements.")

    # If no school_class_id and no subject, it must be school-wide
    if not announcement_in.school_class_id and not announcement_in.subject:
        announcement_in.is_school_wide = True

    try:
        announcement = crud.crud_announcement.create_announcement(
            db=db,
            announcement_in=announcement_in,
            created_by_user_id=current_superuser.id
        )
        return announcement
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to create announcement: {str(e)}")


@router.get(
    "/",
    response_model=List[schemas.Announcement],
    summary="Admin: Get all announcements (school-wide, class-specific, subject-specific)"
)
def get_all_announcements_by_admin(
    is_school_wide: Optional[bool] = Query(None, description="Filter by school-wide status."),
    class_code: Optional[str] = Query(None, description="Filter by class code."),
    subject: Optional[str] = Query(None, description="Filter by subject."),
    db: Session = Depends(get_db),
    current_superuser: models.User = Depends(deps.get_current_active_superuser)
):
    """
    Allows a superuser to retrieve all announcements, with optional filters.
    """
    if is_school_wide is True:
        if class_code or subject:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot filter by class_code or subject when is_school_wide is True.")
        announcements = crud.crud_announcement.get_school_wide_announcements(db)
        return announcements

    if class_code:
        db_class = crud.crud_school_class.get_school_class_orm_by_class_code(db, class_code=class_code)
        if not db_class:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Class with code '{class_code}' not found.")
        
        if subject:
            announcements = crud.crud_announcement.get_subject_announcements_for_class(db, school_class_id=db_class.id, subject=subject)
        else:
            announcements = crud.crud_announcement.get_class_announcements(db, school_class_id=db_class.id)
        return announcements

    if subject and not class_code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot filter by subject without a class_code.")

    if is_school_wide is False:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="When is_school_wide is False, a class_code must be provided.")

    announcements = crud.crud_announcement.get_announcements(db)
    
    return announcements


@router.put(
    "/{announcement_id}",
    response_model=schemas.Announcement,
    summary="Admin: Update an existing announcement"
)
def update_announcement_by_admin(
    announcement_id: int,
    announcement_in: schemas.AnnouncementUpdate,
    db: Session = Depends(get_db),
    current_superuser: models.User = Depends(deps.get_current_active_superuser)
):
    """
    Allows a superuser to update an existing announcement.
    """
    db_announcement = crud.crud_announcement.get_announcement(db, announcement_id=announcement_id)
    if not db_announcement:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Announcement not found.")

    # Handle logic for school_class_id and subject changes
    if announcement_in.school_class_id and announcement_in.school_class_id != db_announcement.school_class_id:
        db_class = crud.crud_school_class.get_school_class_orm_by_id(db, class_id=announcement_in.school_class_id)
        if not db_class:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"New class with ID '{announcement_in.school_class_id}' not found.")
        
        if announcement_in.is_school_wide is True:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot set school_class_id for a school-wide announcement.")

    if announcement_in.subject and announcement_in.subject != db_announcement.subject:
        if not announcement_in.school_class_id and not db_announcement.school_class_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot change subject for a school-wide announcement without specifying a class.")

    try:
        updated_announcement = crud.crud_announcement.update_announcement(db=db, db_announcement=db_announcement, announcement_in=announcement_in)
        return updated_announcement
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to update announcement: {str(e)}")


@router.delete(
    "/{announcement_id}",
    response_model=schemas.Announcement,
    summary="Admin: Delete an announcement"
)
def delete_announcement_by_admin(
    announcement_id: int,
    db: Session = Depends(get_db),
    current_superuser: models.User = Depends(deps.get_current_active_superuser)
):
    """
    Allows a superuser to delete an announcement.
    """
    db_announcement = crud.crud_announcement.get_announcement(db, announcement_id=announcement_id)
    if not db_announcement:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Announcement not found.")

    try:
        deleted_announcement = crud.crud_announcement.delete_announcement(db=db, announcement_id=announcement_id)
        return deleted_announcement
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to delete announcement: {str(e)}")
