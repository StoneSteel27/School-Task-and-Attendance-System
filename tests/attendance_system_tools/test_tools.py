import pytest
import math
from unittest.mock import patch, MagicMock
from attendance_system_tools.webauthn_handler import WebAuthnHandler, TEMP_USER_CREDENTIALS_STORE, TEMP_CHALLENGE_STORE
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

# Clear stores before each test to ensure isolation
@pytest.fixture(autouse=True)
def clear_webauthn_stores():
    TEMP_USER_CREDENTIALS_STORE.clear()
    TEMP_CHALLENGE_STORE.clear()

# --- WebAuthnHandler Tests ---
@pytest.fixture
def webauthn_handler():
    return WebAuthnHandler(rp_id="example.com", rp_name="Example App", rp_origin="https://example.com")

def test_generate_registration_challenge(webauthn_handler):
    user_id = "test_user_id"
    username = "test_username"
    user_display_name = "Test User"
    
    options_json = webauthn_handler.generate_registration_challenge(user_id, username, user_display_name)
    
    assert isinstance(options_json, str)
    options = json.loads(options_json)
    assert options["rp"]["id"] == "example.com"
    assert options["user"]["name"] == username
    assert options["user"]["displayName"] == user_display_name
    assert options["challenge"] is not None

    challenge_bytes = base64.urlsafe_b64decode(options["challenge"] + "==")
    # Check if challenge is stored
    assert challenge_bytes.hex() in TEMP_CHALLENGE_STORE
    stored_challenge_data = TEMP_CHALLENGE_STORE[challenge_bytes.hex()]
    assert stored_challenge_data["app_user_id"] == user_id
    assert stored_challenge_data["type"] == "registration"

@patch('attendance_system_tools.webauthn_handler.verify_registration_response')
def test_verify_registration_response_success(mock_verify_registration_response, webauthn_handler):
    user_id = "test_user_id_reg"
    username = "test_username_reg"
    user_display_name = "Test User Reg"
    
    options_json = webauthn_handler.generate_registration_challenge(user_id, username, user_display_name)
    options = json.loads(options_json)
    challenge_bytes = base64.urlsafe_b64decode(options["challenge"] + "==")
    stored_challenge_hex = challenge_bytes.hex()

    # Simulate a successful client response
    mock_credential_id = b'\x01\x02\x03\x04'
    mock_public_key = b'\x05\x06\x07\x08'
    mock_sign_count = 1
    mock_user_handle = user_id.encode('utf-8')

    mock_verified_credential = MagicMock()
    mock_verified_credential.credential_id = mock_credential_id
    mock_verified_credential.credential_public_key = mock_public_key
    mock_verified_credential.sign_count = mock_sign_count
    mock_verified_credential.user_handle = mock_user_handle
    
    mock_verify_registration_response.return_value = mock_verified_credential

    # Simulate a minimal client response JSON
    client_response_json = {
        "id": base64.urlsafe_b64encode(mock_credential_id).decode('utf-8'),
        "rawId": base64.urlsafe_b64encode(mock_credential_id).decode('utf-8'),
        "response": {
            "clientDataJSON": base64.urlsafe_b64encode(b'{"challenge":"' + options['challenge'].encode('utf-8') + b'"}').decode('utf-8'),
            "attestationObject": base64.urlsafe_b64encode(b'attestation_object').decode('utf-8'),
            "transports": ["usb"]
        },
        "type": "public-key"
    }
    
    result = webauthn_handler.verify_registration_response(
        credential_creation_response_json=json.dumps(client_response_json),
        stored_challenge_hex=stored_challenge_hex
    )
    
    assert result["verified"] == True
    assert result["user_id"] == user_id
    assert result["credential_id_b64"] == base64.urlsafe_b64encode(mock_credential_id).decode('utf-8').rstrip("=")
    
    # Verify credential is stored
    assert user_id in TEMP_USER_CREDENTIALS_STORE
    stored_creds = TEMP_USER_CREDENTIALS_STORE[user_id]
    assert len(stored_creds) == 1
    assert stored_creds[0]["credential_id"] == mock_credential_id
    assert stored_creds[0]["public_key"] == mock_public_key
    assert stored_creds[0]["sign_count"] == mock_sign_count
    assert stored_creds[0]["transports"] == ["usb"]
    assert stored_creds[0]["webauthn_user_handle"] == mock_user_handle

    # Verify challenge is removed
    assert stored_challenge_hex not in TEMP_CHALLENGE_STORE

def test_verify_registration_response_invalid_challenge(webauthn_handler):
    with pytest.raises(ValueError, match="Invalid or expired challenge for registration."):
        webauthn_handler.verify_registration_response("{}", "invalid_challenge_hex")

@patch('attendance_system_tools.webauthn_handler.verify_registration_response')
def test_verify_registration_response_webauthn_exception(mock_verify_registration_response, webauthn_handler):
    user_id = "test_user_id_fail"
    options_json = webauthn_handler.generate_registration_challenge(user_id, "u", "d")
    options = json.loads(options_json)
    challenge_bytes = base64.urlsafe_b64decode(options["challenge"] + "==")
    stored_challenge_hex = challenge_bytes.hex()

    mock_verify_registration_response.side_effect = WebAuthnException("Test WebAuthn Error")

    client_response_json = {
        "id": "some_id", "rawId": "some_raw_id", "response": {"clientDataJSON": "e30", "attestationObject": "e30"}, "type": "public-key"
    }
    
    with pytest.raises(ValueError, match="WebAuthn registration verification failed: Test WebAuthn Error"):
        webauthn_handler.verify_registration_response(json.dumps(client_response_json), stored_challenge_hex)

def test_generate_authentication_challenge_no_credentials(webauthn_handler):
    with pytest.raises(ValueError, match="No WebAuthn credentials registered for user 'non_existent_user'."):
        webauthn_handler.generate_authentication_challenge("non_existent_user")

def test_generate_authentication_challenge_success(webauthn_handler):
    user_id = "auth_user"
    # Manually add a credential for the user
    TEMP_USER_CREDENTIALS_STORE[user_id] = [{
        "credential_id": b'\x11\x22\x33\x44',
        "public_key": b'\x55\x66\x77\x88',
        "sign_count": 10,
        "transports": ["internal"],
    }]

    options_json = webauthn_handler.generate_authentication_challenge(user_id)
    assert isinstance(options_json, str)
    options = json.loads(options_json)
    assert options["rpId"] == "example.com"
    assert options["challenge"] is not None
    assert len(options["allowCredentials"]) == 1
    assert options["allowCredentials"][0]["id"] == base64.urlsafe_b64encode(b'\x11\x22\x33\x44').decode('utf-8').rstrip("=")
    assert options["allowCredentials"][0]["transports"] == ["internal"]

    # Check if challenge is stored
    challenge_bytes = base64.urlsafe_b64decode(options["challenge"] + "==")
    assert challenge_bytes.hex() in TEMP_CHALLENGE_STORE
    stored_challenge_data = TEMP_CHALLENGE_STORE[challenge_bytes.hex()]
    assert stored_challenge_data["app_user_id"] == user_id
    assert stored_challenge_data["type"] == "authentication"

@patch('attendance_system_tools.webauthn_handler.verify_authentication_response')
def test_verify_authentication_response_success(mock_verify_authentication_response, webauthn_handler):
    user_id = "auth_user_verify"
    cred_id_bytes = b'\xaa\xbb\xcc\xdd'
    public_key_bytes = b'\xee\xff\x11\x22'
    initial_sign_count = 5

    TEMP_USER_CREDENTIALS_STORE[user_id] = [{
        "credential_id": cred_id_bytes,
        "public_key": public_key_bytes,
        "sign_count": initial_sign_count,
        "transports": ["usb"],
    }]

    options_json = webauthn_handler.generate_authentication_challenge(user_id)
    options = json.loads(options_json)
    challenge_bytes = base64.urlsafe_b64decode(options["challenge"] + "==")
    stored_challenge_hex = challenge_bytes.hex()

    new_sign_count = initial_sign_count + 1
    mock_verified_auth = MagicMock()
    mock_verified_auth.new_sign_count = new_sign_count
    mock_verify_authentication_response.return_value = mock_verified_auth

    # Simulate client authentication response
    client_auth_response_json = {
        "id": base64.urlsafe_b64encode(cred_id_bytes).decode('utf-8'),
        "rawId": base64.urlsafe_b64encode(cred_id_bytes).decode('utf-8'),
        "response": {
            "clientDataJSON": base64.urlsafe_b64encode(b'{"challenge":"' + options['challenge'].encode('utf-8') + b'"}').decode('utf-8'),
            "authenticatorData": base64.urlsafe_b64encode(b'auth_data').decode('utf-8'),
            "signature": base64.urlsafe_b64encode(b'signature').decode('utf-8'),
        },
        "type": "public-key"
    }

    result = webauthn_handler.verify_authentication_response(
        authentication_response_json=json.dumps(client_auth_response_json),
        stored_challenge_hex=stored_challenge_hex,
        requesting_app_user_id=user_id
    )

    assert result["verified"] == True
    assert result["user_id"] == user_id
    assert result["credential_id_b64"] == base64.urlsafe_b64encode(cred_id_bytes).decode('utf-8').rstrip("=")

def test_verify_authentication_response_invalid_challenge(webauthn_handler):
    with pytest.raises(ValueError, match="Invalid or expired challenge for authentication."):
        webauthn_handler.verify_authentication_response("{}", "invalid_challenge_hex", "some_user")

def test_verify_authentication_response_user_id_mismatch(webauthn_handler):
    user_id = "auth_user_mismatch"
    TEMP_USER_CREDENTIALS_STORE[user_id] = [{
        "credential_id": b'\x11\x22\x33\x44',
        "public_key": b'\x55\x66\x77\x88',
        "sign_count": 10,
        "transports": ["internal"],
    }]
    options_json = webauthn_handler.generate_authentication_challenge(user_id)
    options = json.loads(options_json)
    challenge_bytes = base64.urlsafe_b64decode(options["challenge"] + "==")
    stored_challenge_hex = challenge_bytes.hex()

    with pytest.raises(ValueError, match="Challenge user ID mismatch."):
        webauthn_handler.verify_authentication_response(json.dumps({
            "id": "some_id",
            "rawId": "some_raw_id",
            "response": {
                "clientDataJSON": "e30",
                "authenticatorData": "e30",
                "signature": "e30",
                "userHandle": "e30"
            },
            "type": "public-key"
        }), stored_challenge_hex, "wrong_user")

@patch('attendance_system_tools.webauthn_handler.verify_authentication_response')
def test_verify_authentication_response_webauthn_exception(mock_verify_authentication_response, webauthn_handler):
    user_id = "auth_user_webauthn_fail"
    cred_id_bytes = b'\xaa\xbb\xcc\xdd'
    public_key_bytes = b'\xee\xff\x11\x22'
    initial_sign_count = 5

    TEMP_USER_CREDENTIALS_STORE[user_id] = [{
        "credential_id": cred_id_bytes,
        "public_key": public_key_bytes,
        "sign_count": initial_sign_count,
        "transports": ["usb"],
    }]

    options_json = webauthn_handler.generate_authentication_challenge(user_id)
    options = json.loads(options_json)
    challenge_bytes = base64.urlsafe_b64decode(options["challenge"] + "==")
    stored_challenge_hex = challenge_bytes.hex()

    mock_verify_authentication_response.side_effect = WebAuthnException("Auth Failed")

    client_auth_response_json = {
        "id": base64.urlsafe_b64encode(cred_id_bytes).decode('utf-8'),
        "rawId": base64.urlsafe_b64encode(cred_id_bytes).decode('utf-8'),
        "response": {
            "clientDataJSON": base64.urlsafe_b64encode(b'{"challenge":"' + options['challenge'].encode('utf-8') + b'"}').decode('utf-8'),
            "authenticatorData": base64.urlsafe_b64encode(b'auth_data').decode('utf-8'),
            "signature": base64.urlsafe_b64encode(b'signature').decode('utf-8'),
            "userHandle": base64.urlsafe_b64encode(user_id.encode('utf-8')).decode('utf-8')
        },
        "type": "public-key"
    }

    with pytest.raises(ValueError, match="WebAuthn authentication verification failed: Auth Failed"):
        webauthn_handler.verify_authentication_response(json.dumps(client_auth_response_json), stored_challenge_hex, user_id)


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
