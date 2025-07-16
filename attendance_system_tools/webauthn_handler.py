# attendance_system_tools/webauthn_handler.py

import json
import base64
from typing import List, Dict, Any # For type hinting
from webauthn import (
    generate_registration_options,
    verify_registration_response,
    generate_authentication_options,
    verify_authentication_response,
    options_to_json,
)
from webauthn.helpers import parse_registration_credential_json, parse_authentication_credential_json
from webauthn.helpers.structs import (
    AttestationConveyancePreference,
    AuthenticatorAttachment,
    AuthenticatorSelectionCriteria,
    PublicKeyCredentialCreationOptions,
    PublicKeyCredentialRequestOptions,
    UserVerificationRequirement,
    RegistrationCredential,
    AuthenticationCredential, # For parsing the client's authentication response
    PublicKeyCredentialDescriptor, # For allow_credentials in auth options
    AuthenticatorTransport,
    PublicKeyCredentialType,
)
from webauthn.helpers.exceptions import WebAuthnException


def base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('utf-8')

# A (very) simple in-memory store for demonstration purposes.
# In a real application, you would use a database to store user credentials.
# TEMP_USER_CREDENTIALS_STORE:
#   key: user_id (string, e.g., email or app-specific user ID)
#   value: list of credential dicts, where each dict is:
#          {
#              "credential_id": bytes, # The raw ID of the credential
#              "public_key": bytes,    # The public key associated with the credential
#              "sign_count": int,      # The signature counter
#              "transports": list[str] # Optional: list of transport methods
#          }
TEMP_USER_CREDENTIALS_STORE: Dict[str, List[Dict[str, Any]]] = {}

# TEMP_CHALLENGE_STORE:
#   key: challenge_hex (string)
#   value: dict {"user_id": str, "type": "registration" | "authentication", ...}
TEMP_CHALLENGE_STORE: Dict[str, Dict[str, Any]] = {}


class WebAuthnHandler:
    def __init__(self, rp_id: str, rp_name: str, rp_origin: str):
        if not rp_id or not rp_name or not rp_origin:
            raise ValueError("RP ID, RP Name, and RP Origin cannot be empty.")

        self.rp_id = rp_id
        self.rp_name = rp_name
        self.rp_origin = rp_origin
        print(f"WebAuthnHandler initialized for RP: '{self.rp_name}' (ID: {self.rp_id}, Origin: {self.rp_origin})")

    def generate_registration_challenge(self, user_id: str, username: str, user_display_name: str) -> str:
        # user_id here is the application's user identifier (e.g. email).
        # WebAuthn's user.id (user handle) is generated from this, or can be a separate opaque ID.
        # For simplicity, we'll use user_id.encode('utf-8') as the WebAuthn user.id
        webauthn_user_handle_bytes = user_id.encode('utf-8')

        options: PublicKeyCredentialCreationOptions = generate_registration_options(
            rp_id=self.rp_id,
            rp_name=self.rp_name,
            user_id=webauthn_user_handle_bytes, # This becomes the user.id (user handle) for WebAuthn
            user_name=username,
            user_display_name=user_display_name,
            attestation=AttestationConveyancePreference.NONE,
            authenticator_selection=AuthenticatorSelectionCriteria(
                authenticator_attachment=AuthenticatorAttachment.PLATFORM,
                user_verification=UserVerificationRequirement.REQUIRED,
                require_resident_key=True
            ),
            timeout=60000,
        )

        challenge = options.challenge
        # Store the original app user_id and the webauthn_user_handle for verification context
        TEMP_CHALLENGE_STORE[challenge.hex()] = {
            "app_user_id": user_id,
            "webauthn_user_handle_hex": webauthn_user_handle_bytes.hex(), # For potential cross-check
            "type": "registration"
        }
        return options_to_json(options)

    def verify_registration_response(
        self,
        credential_creation_response_json: str,
        stored_challenge_hex: str
    ) -> dict:
        challenge_details = TEMP_CHALLENGE_STORE.get(stored_challenge_hex)
        if not challenge_details or challenge_details.get("type") != "registration":
            raise ValueError("Invalid or expired challenge for registration.")

        app_user_id = challenge_details["app_user_id"]
        original_challenge_bytes = bytes.fromhex(stored_challenge_hex)

        try:
            registration_credential = parse_registration_credential_json(credential_creation_response_json)
        except Exception as e:
            raise ValueError(f"Failed to parse client registration response: {e}")

        try:
            verified_credential_data = verify_registration_response(
                credential=registration_credential,
                expected_challenge=original_challenge_bytes,
                expected_origin=self.rp_origin,
                expected_rp_id=self.rp_id,
                require_user_verification=True
            )
        except WebAuthnException as e:
            raise ValueError(f"WebAuthn registration verification failed: {e}")
        except Exception as e:
            raise ValueError(f"An unexpected error occurred during WebAuthn registration verification: {e}")

        new_credential_for_storage = {
            "credential_id": verified_credential_data.credential_id,
            "public_key": verified_credential_data.credential_public_key,
            "sign_count": verified_credential_data.sign_count,
            "transports": [t.value for t in registration_credential.response.transports] if registration_credential.response.transports else [],
            "webauthn_user_handle": bytes.fromhex(challenge_details["webauthn_user_handle_hex"])
        }

        if app_user_id not in TEMP_USER_CREDENTIALS_STORE:
            TEMP_USER_CREDENTIALS_STORE[app_user_id] = []

        existing_ids = [cred["credential_id"] for cred in TEMP_USER_CREDENTIALS_STORE[app_user_id]]
        if verified_credential_data.credential_id in existing_ids:
            raise ValueError("This authenticator (credential ID) has already been registered for this user.")

        TEMP_USER_CREDENTIALS_STORE[app_user_id].append(new_credential_for_storage)
        print(f"Successfully verified and stored new credential for user '{app_user_id}'.")
        print(f"  Credential ID (raw hex): {verified_credential_data.credential_id.hex()}")

        TEMP_CHALLENGE_STORE.pop(stored_challenge_hex, None)

        return {
            "credential_id_b64": base64url_encode(verified_credential_data.credential_id),
            "user_id": app_user_id, # The application's user ID
            "verified": True,
        }

    def generate_authentication_challenge(self, app_user_id: str) -> str:
        """
        Generates PublicKeyCredentialRequestOptions for an existing WebAuthn credential authentication.

        Args:
            app_user_id: The application's unique identifier for the user (e.g., email).

        Returns:
            str: A JSON string representing the options to be sent to the client.
                 The server MUST store the generated challenge to verify the client's response.
        """
        user_credentials = TEMP_USER_CREDENTIALS_STORE.get(app_user_id)
        if not user_credentials:
            # If aiming for discoverable credentials and no specific user_id is known yet (e.g., passwordless login start)
            # you could omit `allow_credentials`. However, for 2FA, user_id is known.
            raise ValueError(f"No WebAuthn credentials registered for user '{app_user_id}'.")

        allowed_credentials_descriptors: List[PublicKeyCredentialDescriptor] = []
        for cred in user_credentials:
            transports = cred.get("transports")
            transport_enums = None
            if transports:
                transport_enums = [AuthenticatorTransport(t) for t in transports]

            allowed_credentials_descriptors.append(
                PublicKeyCredentialDescriptor(type=PublicKeyCredentialType.PUBLIC_KEY, id=cred["credential_id"], transports=transport_enums)
            )

        options: PublicKeyCredentialRequestOptions = generate_authentication_options(
            rp_id=self.rp_id,
            allow_credentials=allowed_credentials_descriptors, # For 2FA, this is usually good.
            user_verification=UserVerificationRequirement.REQUIRED, # Consistent with registration
            timeout=60000,
        )

        challenge = options.challenge
        TEMP_CHALLENGE_STORE[challenge.hex()] = {
            "app_user_id": app_user_id, # To know who initiated this auth attempt
            "type": "authentication"
        }
        return options_to_json(options)

    def verify_authentication_response(
        self,
        authentication_response_json: str, # JSON string from navigator.credentials.get()
        stored_challenge_hex: str, # The challenge (hex) that was stored
        requesting_app_user_id: str # The app user ID we expect to be authenticating (e.g., from session)
    ) -> dict:
        """
        Verifies the client's response to an authentication challenge.

        Args:
            authentication_response_json: The JSON stringified response from navigator.credentials.get().
            stored_challenge_hex: The hex-encoded challenge string stored server-side.
            requesting_app_user_id: The application's user ID for whom authentication is being verified.

        Returns:
            A dictionary indicating successful verification.

        Raises:
            ValueError: If challenge is invalid, response parsing fails, or verification fails.
        """
        challenge_details = TEMP_CHALLENGE_STORE.get(stored_challenge_hex)
        if not challenge_details or challenge_details.get("type") != "authentication":
            raise ValueError("Invalid or expired challenge for authentication.")

        if challenge_details.get("app_user_id") != requesting_app_user_id:
            raise ValueError(f"Challenge user ID mismatch. Expected '{challenge_details.get('app_user_id')}', got '{requesting_app_user_id}'.")

        original_challenge_bytes = bytes.fromhex(stored_challenge_hex)

        try:
            auth_credential_obj = parse_authentication_credential_json(authentication_response_json)
        except Exception as e:
            raise ValueError(f"Failed to parse client authentication response: {e}")

        used_credential_id_bytes = auth_credential_obj.raw_id

        stored_user_credentials = TEMP_USER_CREDENTIALS_STORE.get(requesting_app_user_id)
        if not stored_user_credentials:
            raise ValueError(f"No credentials found for user '{requesting_app_user_id}' during verification.")

        matching_stored_credential = None
        matching_stored_credential_idx = -1
        for cred_idx, cred_data in enumerate(stored_user_credentials):
            if cred_data["credential_id"] == used_credential_id_bytes:
                matching_stored_credential = cred_data
                matching_stored_credential_idx = cred_idx
                break

        if not matching_stored_credential:
            raise ValueError(
                f"Credential ID '{base64url_encode(used_credential_id_bytes)}' "
                f"not registered for user '{requesting_app_user_id}'."
            )

        credential_public_key_bytes = matching_stored_credential["public_key"]
        credential_current_sign_count = matching_stored_credential["sign_count"]
        expected_webauthn_user_handle = matching_stored_credential.get("webauthn_user_handle")

        response_user_handle_bytes = auth_credential_obj.response.user_handle

        if response_user_handle_bytes is not None and expected_webauthn_user_handle is not None:
            if response_user_handle_bytes != expected_webauthn_user_handle:
                raise ValueError(
                    f"User handle mismatch. Authenticator response: '{response_user_handle_bytes.hex()}', "
                    f"Expected for credential: '{expected_webauthn_user_handle.hex()}'"
                )
        elif response_user_handle_bytes is None and expected_webauthn_user_handle is not None and self.rp_id == self.rp_origin:
             pass

        try:
            verified_authentication = verify_authentication_response(
                credential=auth_credential_obj,
                expected_challenge=original_challenge_bytes,
                expected_rp_id=self.rp_id,
                expected_origin=self.rp_origin,
                credential_public_key=credential_public_key_bytes,
                credential_current_sign_count=credential_current_sign_count,
                require_user_verification=True
            )
            new_sign_count = verified_authentication.new_sign_count
        except WebAuthnException as e:
            raise ValueError(f"WebAuthn authentication verification failed: {e}")
        except Exception as e:
            raise ValueError(f"Unexpected error during WebAuthn authentication verification: {e}")

        TEMP_USER_CREDENTIALS_STORE[requesting_app_user_id][matching_stored_credential_idx]["sign_count"] = new_sign_count
        print(f"Successfully verified authentication for user '{requesting_app_user_id}'.")
        print(f"  Credential ID (raw hex): {used_credential_id_bytes.hex()}")
        print(f"  New sign count: {new_sign_count}")

        TEMP_CHALLENGE_STORE.pop(stored_challenge_hex, None)

        return {
            "verified": True,
            "user_id": requesting_app_user_id,
            "credential_id_b64": base64url_encode(used_credential_id_bytes)
        }
