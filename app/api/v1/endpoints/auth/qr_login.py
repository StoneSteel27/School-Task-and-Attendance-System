import uuid
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api import deps
from app.db.session import get_db
from app import models, schemas
from app.schemas.auth import qr_login as qr_login_schema
from app.core.security import create_access_token
from app.crud.auth import qr_login_session as crud_qr_login_session

router = APIRouter()


@router.post("/qr-login/start", response_class=Response)
def qr_login_start(db: Session = Depends(get_db)):
    """
    Initiates a QR code login flow for a new device.

    Generates a unique token, stores it, and returns it as a QR code image.
    The new device should display this QR code to be scanned by an authenticated device.
    """
    token = uuid.uuid4().hex
    crud_qr_login_session.create_qr_login_session(db, obj_in=schemas.qr_login_session.QRLoginSessionCreate(token=token))

    # Generate the QR code image containing the token
    image_bytes = deps.qr_code_manager.generate_qr_code_image(data=token)

    return Response(content=image_bytes, media_type="image/png")


@router.post("/qr-login/approve")
def qr_login_approve(
    *,
    db: Session = Depends(get_db),
    approval_data: qr_login_schema.QRLoginApproveRequest,
    current_user: models.User = Depends(deps.get_current_active_user)
):
    """
    Approves a QR code login request from an authenticated device.

    This is called by the authenticated mobile app after scanning the QR code.
    """
    token = approval_data.token
    session = crud_qr_login_session.get_qr_login_session_by_token(db, token=token)

    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Login session not found or expired.")

    if session.status != "pending":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Login session is not pending (status: {session.status}).")

    # Check for timeout (e.g., 5 minutes)
    if datetime.utcnow() - session.created_at > timedelta(minutes=5):
        crud_qr_login_session.update_qr_login_session(db, db_obj=session, obj_in={"status": "expired"})
        raise HTTPException(status_code=status.HTTP_408_REQUEST_TIMEOUT, detail="Login session has expired.")

    # Generate a new access token for the device that initiated the QR login
    new_access_token = create_access_token(data={"sub": current_user.email})

    # Update the session to "approved" and store the new token
    crud_qr_login_session.update_qr_login_session(
        db,
        db_obj=session,
        obj_in=schemas.qr_login_session.QRLoginSessionUpdate(status="approved", user_id=current_user.id)
    )

    return {"status": "success", "detail": "Login approved for the new device."}


@router.get("/qr-login/poll/{token}", response_model=qr_login_schema.QRLoginPollResponse)
def qr_login_poll(token: str, db: Session = Depends(get_db)):
    """
    Polls for the status of a QR code login request.

    This is called by the new (unauthenticated) device to check if the login
    has been approved by the authenticated device.
    """
    session = crud_qr_login_session.get_qr_login_session_by_token(db, token=token)

    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Login session not found or expired.")

    if session.status == "approved":
        # Generate access token
        user = session.user
        access_token = create_access_token(data={"sub": user.email})
        
        # Return the access token and clear the session to prevent reuse
        response = qr_login_schema.QRLoginPollResponse(
            status="approved",
            access_token=access_token
        )
        db.delete(session)
        db.commit()
        return response

    # Check for timeout
    if datetime.utcnow() - session.created_at > timedelta(minutes=5):
        crud_qr_login_session.update_qr_login_session(db, db_obj=session, obj_in={"status": "expired"})

    return qr_login_schema.QRLoginPollResponse(status=session.status)


@router.post("/qr-login/cleanup")
def qr_login_cleanup(db: Session = Depends(get_db)):
    """
    Cleans up expired QR code login sessions from the database.
    """
    crud_qr_login_session.cleanup_expired_sessions(db)
    return {"status": "success", "detail": "Expired sessions cleaned up."}
