import uuid
import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api import deps
from app.db.session import get_db
from app import models
from app.schemas import qr_login as qr_login_schema
from app.core.security import create_access_token

router = APIRouter()

# --- QR Code Based Login Flow ---

@router.post("/qr-login/start", response_class=Response)
def qr_login_start():
    """
    Initiates a QR code login flow for a new device.
    
    Generates a unique token, stores it, and returns it as a QR code image.
    The new device should display this QR code to be scanned by an authenticated device.
    """
    token = uuid.uuid4().hex
    
    # Store the token with a pending status and a timestamp
    deps.QR_LOGIN_SESSIONS[token] = {
        "status": "pending",
        "user_id": None,
        "access_token": None,
        "created_at": datetime.datetime.utcnow()
    }
    
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
    session = deps.QR_LOGIN_SESSIONS.get(token)
    
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Login session not found or expired.")
        
    if session["status"] != "pending":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Login session is not pending (status: {session['status']}).")

    # Check for timeout (e.g., 5 minutes)
    if datetime.datetime.utcnow() - session["created_at"] > datetime.timedelta(minutes=5):
        session["status"] = "expired"
        raise HTTPException(status_code=status.HTTP_408_REQUEST_TIMEOUT, detail="Login session has expired.")

    # Generate a new access token for the device that initiated the QR login
    new_access_token = create_access_token(data={"sub": current_user.email})
    
    # Update the session to "approved" and store the new token
    session["status"] = "approved"
    session["user_id"] = current_user.id
    session["access_token"] = new_access_token
    
    return {"status": "success", "detail": "Login approved for the new device."}


@router.get("/qr-login/poll/{token}", response_model=qr_login_schema.QRLoginPollResponse)
def qr_login_poll(token: str):
    """
    Polls for the status of a QR code login request.
    
    This is called by the new (unauthenticated) device to check if the login
    has been approved by the authenticated device.
    """
    session = deps.QR_LOGIN_SESSIONS.get(token)
    
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Login session not found or expired.")

    if session["status"] == "approved":
        # Return the access token and clear the session to prevent reuse
        response = qr_login_schema.QRLoginPollResponse(
            status="approved",
            access_token=session["access_token"]
        )
        del deps.QR_LOGIN_SESSIONS[token]
        return response
        
    # Check for timeout
    if datetime.datetime.utcnow() - session["created_at"] > datetime.timedelta(minutes=5):
        session["status"] = "expired"

    return qr_login_schema.QRLoginPollResponse(status=session["status"])
