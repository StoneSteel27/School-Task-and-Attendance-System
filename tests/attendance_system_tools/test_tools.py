import pytest
from app.core.security import get_password_hash
import math
from unittest.mock import patch, MagicMock
from attendance_system_tools.webauthn_handler import WebAuthnHandler
from attendance_system_tools.qr_code_manager import QRCodeManager
from attendance_system_tools.recovery_codes_manager import RecoveryCodesManager
from attendance_system_tools.geofence_manager import GeofenceManager
from webauthn.helpers.structs import (
    PublicKeyCredentialCreationOptions,
    PublicKeyCredentialRequestOptions,
    RegistrationCredential,
    AuthenticationCredential,
)
from webauthn.helpers.exceptions import WebAuthnException
import base64
import json
from shapely.geometry import Point, Polygon
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.user import User
from app.crud import crud_user, crud_webauthn
from app.schemas.user import UserCreate

# Database fixture
@pytest.fixture(scope="session")
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

from app.core.security import get_password_hash

# ... (other imports)

# Test user fixture
@pytest.fixture(scope="session")
def test_user(db_session: Session):
    user_email = "webauthn_test@example.com"
    user = crud_user.get_user_by_email(db_session, email=user_email)
    if not user:
        user_in = UserCreate(email=user_email, password="password", full_name="WebAuthn Test User", roll_number="W123")
        password_hash = get_password_hash("password")
        user = crud_user.create_user(db_session, user_in=user_in, password_hash=password_hash)
    return user

# --- WebAuthnHandler Tests ---
@pytest.fixture
def webauthn_handler(db_session: Session):
    # Clean up any old data before a test run
    db_session.query(crud_webauthn.WebAuthnCredential).delete()
    db_session.query(crud_webauthn.WebAuthnChallenge).delete()
    db_session.commit()
    return WebAuthnHandler(rp_id="localhost", rp_name="Test App", rp_origin="http://localhost", db=db_session)

def test_generate_registration_challenge(webauthn_handler: WebAuthnHandler, test_user: User, db_session: Session):
    options_json = webauthn_handler.generate_registration_challenge(
        user_id=test_user.id,
        username=test_user.email,
        user_display_name=test_user.full_name
    )
    options = json.loads(options_json)
    challenge_bytes = base64.urlsafe_b64decode(options["challenge"] + "==")
    challenge_hex = challenge_bytes.hex()
    
    db_challenge = crud_webauthn.get_challenge(db_session, challenge_hex)
    assert db_challenge is not None
    assert db_challenge.challenge == challenge_hex
    crud_webauthn.remove_challenge(db_session, challenge_hex)

@patch('attendance_system_tools.webauthn_handler.verify_registration_response')
def test_verify_registration_response_success(mock_verify, webauthn_handler: WebAuthnHandler, test_user: User, db_session: Session):
    options_json = webauthn_handler.generate_registration_challenge(
        user_id=test_user.id,
        username=test_user.email,
        user_display_name=test_user.full_name
    )
    options = json.loads(options_json)
    challenge_hex = base64.urlsafe_b64decode(options["challenge"] + "==").hex()

    mock_credential_id = b'\x01\x02\x03\x04'
    mock_public_key = b'\x05\x06\x07\x08'
    
    mock_verified_credential = MagicMock()
    mock_verified_credential.credential_id = mock_credential_id
    mock_verified_credential.credential_public_key = mock_public_key
    mock_verified_credential.sign_count = 1
    mock_verify.return_value = mock_verified_credential

    client_response = {
        "id": "test_id",
        "rawId": "test_raw_id",
        "response": {
            "clientDataJSON": "client_data",
            "attestationObject": "attestation_object"
        },
        "type": "public-key"
    }
    
    result = webauthn_handler.verify_registration_response(
        credential_creation_response_json=json.dumps(client_response),
        stored_challenge_hex=challenge_hex,
        user_id=test_user.id
    )
    
    assert result["verified"] is True
    db_cred = crud_webauthn.get_credential_by_id(db_session, mock_credential_id)
    assert db_cred is not None
    assert db_cred.user_id == test_user.id
    assert db_cred.public_key == mock_public_key

def test_generate_authentication_challenge_success(webauthn_handler: WebAuthnHandler, test_user: User, db_session: Session):
    # Ensure user has a credential first
    cred_in = {"user_id": test_user.id, "credential_id": b'\x11\x22\x33', "public_key": b'\x44\x55\x66', "sign_count": 0}
    crud_webauthn.create_credential(db_session, obj_in=crud_webauthn.WebAuthnCredentialCreate(**cred_in))
    
    options_json = webauthn_handler.generate_authentication_challenge(user_id=test_user.id)
    options = json.loads(options_json)
    challenge_hex = base64.urlsafe_b64decode(options["challenge"] + "==").hex()
    
    db_challenge = crud_webauthn.get_challenge(db_session, challenge_hex)
    assert db_challenge is not None
    crud_webauthn.remove_challenge(db_session, challenge_hex)

@patch('attendance_system_tools.webauthn_handler.verify_authentication_response')
def test_verify_authentication_response_success(mock_verify, webauthn_handler: WebAuthnHandler, test_user: User, db_session: Session):
    cred_id = b'\xaa\xbb\xcc'
    cred_in = {"user_id": test_user.id, "credential_id": cred_id, "public_key": b'\xdd\xee\xff', "sign_count": 5}
    cred = crud_webauthn.create_credential(db_session, obj_in=crud_webauthn.WebAuthnCredentialCreate(**cred_in))

    options_json = webauthn_handler.generate_authentication_challenge(user_id=test_user.id)
    options = json.loads(options_json)
    challenge_hex = base64.urlsafe_b64decode(options["challenge"] + "==").hex()

    mock_verified_auth = MagicMock()
    mock_verified_auth.new_sign_count = 6
    mock_verify.return_value = mock_verified_auth

    # We need to mock parse_authentication_credential_json to return a mock object with a raw_id
    with patch('attendance_system_tools.webauthn_handler.parse_authentication_credential_json') as mock_parse:
        mock_parsed_cred = MagicMock()
        mock_parsed_cred.raw_id = cred_id
        mock_parse.return_value = mock_parsed_cred

        client_response = {"rawId": base64.urlsafe_b64encode(cred_id).decode()}
        
        result = webauthn_handler.verify_authentication_response(
            authentication_response_json=json.dumps(client_response),
            stored_challenge_hex=challenge_hex,
            user_id=test_user.id
        )
    
    assert result["verified"] is True
    db_session.refresh(cred)
    assert cred.sign_count == 6


# --- QRCodeManager Tests ---
@pytest.fixture
def qr_code_manager():
    return QRCodeManager()

def test_generate_qr_code_image_png(qr_code_manager):
    data = "Hello QR Code!"
    image_bytes = qr_code_manager.generate_qr_code_image(data, image_format='PNG')
    assert isinstance(image_bytes, bytes)
    assert len(image_bytes) > 0
    # Basic check for PNG header (first few bytes)
    assert image_bytes[:8] == b'\x89PNG\r\n\x1a\n'

def test_generate_qr_code_image_jpeg(qr_code_manager):
    data = "JPEG Test"
    image_bytes = qr_code_manager.generate_qr_code_image(data, image_format='JPEG')
    assert isinstance(image_bytes, bytes)
    assert len(image_bytes) > 0
    # Basic check for JPEG header (first few bytes)
    assert image_bytes[:3] == b'\xff\xd8\xff'

def test_generate_qr_code_image_empty_data(qr_code_manager):
    with pytest.raises(ValueError, match="Data for QR code cannot be empty."):
        qr_code_manager.generate_qr_code_image("")

def test_generate_qr_code_image_unsupported_format(qr_code_manager):
    with pytest.raises(ValueError, match=r"Unsupported image format: SVG. Supported: \['PNG', 'JPEG', 'BMP', 'GIF', 'TIFF'\]"):
        qr_code_manager.generate_qr_code_image("test", image_format='SVG')

def test_generate_qr_code_image_custom_colors(qr_code_manager):
    data = "Custom Colors"
    image_bytes = qr_code_manager.generate_qr_code_image(data, fill_color="red", back_color="blue")
    assert isinstance(image_bytes, bytes)
    assert len(image_bytes) > 0
    # More advanced checks would involve image processing to verify colors,
    # but for a unit test, checking byte content and no errors is sufficient.


# --- RecoveryCodesManager Tests ---
@pytest.fixture
def recovery_codes_manager():
    return RecoveryCodesManager()

def test_generate_recovery_codes_default(recovery_codes_manager):
    codes = recovery_codes_manager.generate_recovery_codes(count=5)
    assert len(codes) == 5
    assert len(set(codes)) == 5 # Ensure uniqueness
    for code in codes:
        assert isinstance(code, str)
        assert len(code.replace('-', '')) == recovery_codes_manager.expected_normalized_length
        assert '-' in code # Check separator

def test_generate_recovery_codes_custom_params():
    manager = RecoveryCodesManager(num_segments=2, segment_length=4, separator='*', character_set="ABCDE")
    codes = manager.generate_recovery_codes(count=3)
    assert len(codes) == 3
    assert len(set(codes)) == 3
    for code in codes:
        assert len(code.replace('*', '')) == 8 # 2 * 4
        assert '*' in code
        assert all(c in "ABCDE" for c in code if c != '*')

def test_generate_recovery_codes_invalid_count():
    manager = RecoveryCodesManager()
    with pytest.raises(ValueError, match="Number of codes to generate must be positive."):
        manager.generate_recovery_codes(count=0)

def test_get_code_hash_success(recovery_codes_manager):
    code = "ABCDE-FGHJK-LMNPQ" # Example code matching default format
    hashed_code = recovery_codes_manager.get_code_hash(code)
    assert isinstance(hashed_code, str)
    assert len(hashed_code) == 64 # SHA256 hex digest length

    # Test normalization (case-insensitivity, separator removal)
    hashed_code_normalized = recovery_codes_manager.get_code_hash("abcde-fghjk-lmnpq")
    assert hashed_code == hashed_code_normalized

    hashed_code_no_separator = recovery_codes_manager.get_code_hash("ABCDEFGHJKLMNPQ")
    assert hashed_code == hashed_code_no_separator

def test_get_code_hash_invalid_length(recovery_codes_manager):
    with pytest.raises(ValueError, match="Normalized code 'SHORT' has length 5, but expected length is 15"):
        recovery_codes_manager.get_code_hash("SHORT")

def test_get_code_hash_invalid_character():
    manager = RecoveryCodesManager(character_set="ABC", num_segments=1, segment_length=3)
    with pytest.raises(ValueError, match="contains an invalid character 'D'"):
        manager.get_code_hash("ABD")

def test_get_code_hash_empty_string(recovery_codes_manager):
    with pytest.raises(ValueError, match="Code string to hash cannot be empty."):
        recovery_codes_manager.get_code_hash("")

# --- GeofenceManager Tests ---
@pytest.fixture
def geofence_manager():
    return GeofenceManager()

def test_is_within_radius_true(geofence_manager):
    # Center of a city, radius 1km
    center_lat, center_lon = 34.0522, -118.2437
    radius = 1000 # meters

    # A point very close to the center
    current_lat, current_lon = 34.05225, -118.24375
    assert geofence_manager.is_within_radius(current_lat, current_lon, center_lat, center_lon, radius) == True

def test_is_within_radius_false(geofence_manager):
    center_lat, center_lon = 34.0522, -118.2437
    radius = 100 # meters

    # A point far away
    current_lat, current_lon = 34.0600, -118.2500
    assert geofence_manager.is_within_radius(current_lat, current_lon, center_lat, center_lon, radius) == False

def test_is_within_radius_edge_case(geofence_manager):
    center_lat, center_lon = 0.0, 0.0
    radius = 1 # meter

    # A point exactly 1 meter away (approx 0.000009 degrees lat/lon)
    # Due to floating point precision, use a small tolerance or check for very close values
    # For simplicity, let's pick a point slightly inside
    current_lat, current_lon = 0.000001, 0.000001
    assert geofence_manager.is_within_radius(current_lat, current_lon, center_lat, center_lon, radius) == True

def test_is_within_polygon_true(geofence_manager):
    # A simple square polygon
    polygon_coords = [(0, 0), (0, 10), (10, 10), (10, 0)] # (lon, lat)
    
    # Point inside
    current_lat, current_lon = 5, 5
    assert geofence_manager.is_within_polygon(current_lat, current_lon, polygon_coords) == True

def test_is_within_polygon_false(geofence_manager):
    polygon_coords = [(0, 0), (0, 10), (10, 10), (10, 0)]
    
    # Point outside
    current_lat, current_lon = 15, 5
    assert geofence_manager.is_within_polygon(current_lat, current_lon, polygon_coords) == False

def test_is_within_polygon_on_boundary(geofence_manager):
    polygon_coords = [(0, 0), (0, 10), (10, 10), (10, 0)]
    
    # Point on the edge
    current_lat, current_lon = 0, 5
    assert geofence_manager.is_within_polygon(current_lat, current_lon, polygon_coords) == True # Shapely contains includes boundary

def test_is_within_polygon_invalid_polygon(geofence_manager):
    # Less than 3 coordinates
    polygon_coords = [(0, 0), (1, 1)]
    current_lat, current_lon = 0.5, 0.5
    assert geofence_manager.is_within_polygon(current_lat, current_lon, polygon_coords) == False

def test_check_location_against_geofences_circle_match(geofence_manager):
    geofences = [
        {"id": "home", "name": "Home Circle", "type": "circle", "center_lat": 10.0, "center_lon": 10.0, "radius_meters": 100},
        {"id": "work", "name": "Work Polygon", "type": "polygon", "coordinates": [(20.0, 20.0), (20.0, 30.0), (30.0, 30.0), (30.0, 20.0)]}
    ]
    current_lat, current_lon = 10.00001, 10.00001
    result = geofence_manager.check_location_against_geofences(current_lat, current_lon, geofences)
    assert result["is_within_geofence"] == True
    assert result["matched_geofence"]["id"] == "home"
    assert result["matched_geofence"]["type"] == "circle"

def test_check_location_against_geofences_polygon_match(geofence_manager):
    geofences = [
        {"id": "home", "name": "Home Circle", "type": "circle", "center_lat": 10.0, "center_lon": 10.0, "radius_meters": 100},
        {"id": "work", "name": "Work Polygon", "type": "polygon", "coordinates": [(20.0, 20.0), (20.0, 30.0), (30.0, 30.0), (30.0, 20.0)]}
    ]
    current_lat, current_lon = 25, 25 # Inside work polygon
    result = geofence_manager.check_location_against_geofences(current_lat, current_lon, geofences)
    assert result["is_within_geofence"] == True
    assert result["matched_geofence"]["id"] == "work"
    assert result["matched_geofence"]["type"] == "polygon"

def test_check_location_against_geofences_no_match(geofence_manager):
    geofences = [
        {"id": "home", "name": "Home Circle", "type": "circle", "center_lat": 10.0, "center_lon": 10.0, "radius_meters": 100},
        {"id": "work", "name": "Work Polygon", "type": "polygon", "coordinates": [(20.0, 20.0), (20.0, 30.0), (30.0, 30.0), (30.0, 20.0)]}
    ]
    current_lat, current_lon = 50, 50 # Far away
    result = geofence_manager.check_location_against_geofences(current_lat, current_lon, geofences)
    assert result["is_within_geofence"] == False
    assert result["matched_geofence"] is None

def test_check_location_against_geofences_mixed_types_and_order(geofence_manager):
    geofences = [
        {"id": "park", "name": "Park Polygon", "type": "polygon", "coordinates": [(5.0, 5.0), (5.0, 15.0), (15.0, 15.0), (15.0, 5.0)]},
        {"id": "cafe", "name": "Cafe Circle", "type": "circle", "center_lat": 20.0, "center_lon": 20.0, "radius_meters": 50}
    ]
    
    # Test point inside park
    current_lat_park, current_lon_park = 10, 10
    result_park = geofence_manager.check_location_against_geofences(current_lat_park, current_lon_park, geofences)
    assert result_park["is_within_geofence"] == True
    assert result_park["matched_geofence"]["id"] == "park"

    # Test point inside cafe
    current_lat_cafe, current_lon_cafe = 20.00001, 20.00001
    result_cafe = geofence_manager.check_location_against_geofences(current_lat_cafe, current_lon_cafe, geofences)
    assert result_cafe["is_within_geofence"] == True
    assert result_cafe["matched_geofence"]["id"] == "cafe"

def test_check_location_against_geofences_invalid_geofence_definition(geofence_manager):
    geofences = [
        {"id": "invalid_circle", "type": "circle", "center_lat": 10.0, "center_lon": 10.0}, # Missing radius
        {"id": "invalid_polygon", "type": "polygon", "coordinates": [(0,0), (1,1)]} # Not enough points
    ]
    current_lat, current_lon = 10.0, 10.0
    result = geofence_manager.check_location_against_geofences(current_lat, current_lon, geofences)
    assert result["is_within_geofence"] == False
    assert result["matched_geofence"] is None
