# attendance_system_tools/webauthn_handler.py

import base64
from typing import List, Dict, Any

from sqlalchemy.orm import Session
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
    PublicKeyCredentialDescriptor,
    AuthenticatorTransport,
    PublicKeyCredentialType,
)
from webauthn.helpers.exceptions import WebAuthnException

from app.crud import crud_webauthn
from app.schemas.webauthn import WebAuthnCredentialCreate, WebAuthnCredentialUpdate


def base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('utf-8')


class WebAuthnHandler:
    def __init__(self, rp_id: str, rp_name: str, rp_origin: str, db: Session):
        if not rp_id or not rp_name or not rp_origin:
            raise ValueError("RP ID, RP Name, and RP Origin cannot be empty.")

        self.rp_id = rp_id
        self.rp_name = rp_name
        self.rp_origin = rp_origin
        self.db = db
        print(f"WebAuthnHandler initialized for RP: '{self.rp_name}' (ID: {self.rp_id}, Origin: {self.rp_origin})")

    def generate_registration_challenge(self, user_id: int, username: str, user_display_name: str) -> str:
        webauthn_user_handle_bytes = str(user_id).encode('utf-8')

        options: PublicKeyCredentialCreationOptions = generate_registration_options(
            rp_id=self.rp_id,
            rp_name=self.rp_name,
            user_id=webauthn_user_handle_bytes,
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
        crud_webauthn.create_challenge(self.db, challenge.hex())
        return options_to_json(options)

    def verify_registration_response(
        self,
        credential_creation_response_json: str,
        stored_challenge_hex: str,
        user_id: int
    ) -> dict:
        challenge = crud_webauthn.get_challenge(self.db, stored_challenge_hex)
        if not challenge:
            raise ValueError("Invalid or expired challenge for registration.")

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

        credential_id = verified_credential_data.credential_id
        if crud_webauthn.get_credential_by_id(self.db, credential_id):
            raise ValueError("This authenticator (credential ID) has already been registered for this user.")

        new_credential = WebAuthnCredentialCreate(
            user_id=user_id,
            credential_id=credential_id,
            public_key=verified_credential_data.credential_public_key,
            sign_count=verified_credential_data.sign_count,
        )
        crud_webauthn.create_credential(self.db, new_credential)
        crud_webauthn.remove_challenge(self.db, stored_challenge_hex)

        return {
            "credential_id_b64": base64url_encode(verified_credential_data.credential_id),
            "user_id": user_id,
            "verified": True,
        }

    def generate_authentication_challenge(self, user_id: int) -> str:
        user_credentials = crud_webauthn.get_credentials_by_user_id(self.db, user_id)
        if not user_credentials:
            raise ValueError(f"No WebAuthn credentials registered for user '{user_id}'.")

        allowed_credentials_descriptors: List[PublicKeyCredentialDescriptor] = []
        for cred in user_credentials:
            allowed_credentials_descriptors.append(
                PublicKeyCredentialDescriptor(type=PublicKeyCredentialType.PUBLIC_KEY, id=cred.credential_id)
            )

        options: PublicKeyCredentialRequestOptions = generate_authentication_options(
            rp_id=self.rp_id,
            allow_credentials=allowed_credentials_descriptors,
            user_verification=UserVerificationRequirement.REQUIRED,
            timeout=60000,
        )

        challenge = options.challenge
        crud_webauthn.create_challenge(self.db, challenge.hex())
        return options_to_json(options)

    def verify_authentication_response(
        self,
        authentication_response_json: str,
        stored_challenge_hex: str,
        user_id: int
    ) -> dict:
        challenge = crud_webauthn.get_challenge(self.db, stored_challenge_hex)
        if not challenge:
            raise ValueError("Invalid or expired challenge for authentication.")

        original_challenge_bytes = bytes.fromhex(stored_challenge_hex)

        try:
            auth_credential_obj = parse_authentication_credential_json(authentication_response_json)
        except Exception as e:
            raise ValueError(f"Failed to parse client authentication response: {e}")

        used_credential_id_bytes = auth_credential_obj.raw_id
        stored_credential = crud_webauthn.get_credential_by_id(self.db, used_credential_id_bytes)

        if not stored_credential or stored_credential.user_id != user_id:
            raise ValueError(
                f"Credential ID '{base64url_encode(used_credential_id_bytes)}' "
                f"not registered for user '{user_id}'."
            )

        try:
            verified_authentication = verify_authentication_response(
                credential=auth_credential_obj,
                expected_challenge=original_challenge_bytes,
                expected_rp_id=self.rp_id,
                expected_origin=self.rp_origin,
                credential_public_key=stored_credential.public_key,
                credential_current_sign_count=stored_credential.sign_count,
                require_user_verification=True
            )
            new_sign_count = verified_authentication.new_sign_count
        except WebAuthnException as e:
            raise ValueError(f"WebAuthn authentication verification failed: {e}")
        except Exception as e:
            raise ValueError(f"Unexpected error during WebAuthn authentication verification: {e}")

        update_data = WebAuthnCredentialUpdate(sign_count=new_sign_count)
        crud_webauthn.update_credential(self.db, stored_credential, update_data)
        crud_webauthn.remove_challenge(self.db, stored_challenge_hex)

        return {
            "verified": True,
            "user_id": user_id,
            "credential_id_b64": base64url_encode(used_credential_id_bytes)
        }
