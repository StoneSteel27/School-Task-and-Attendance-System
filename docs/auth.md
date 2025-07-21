# Authentication API Endpoints

## Token Management

### Login for Access Token

*   **HTTP Method:** `POST`
*   **URL Path:** `/auth/login/access-token`
*   **Brief Description:** OAuth2 compatible token login, get an access token for future requests.
*   **Expected Payload/Body (form-data):**
    *   `username`: The user's email.
    *   `password`: The user's password.
*   **Expected Response:**
    ```json
    {
        "access_token": "string",
        "token_type": "bearer"
    }
    ```

## WebAuthn

### Begin WebAuthn Registration

*   **HTTP Method:** `POST`
*   **URL Path:** `/auth/register/webauthn/begin`
*   **Brief Description:** Begin WebAuthn registration by generating a challenge.
*   **Expected Payload/Body:**
    ```json
    {
        "username": "string",
        "display_name": "string"
    }
    ```
*   **Expected Response:**
    ```json
    {
        "challenge": "string",
        "options": { ... }
    }
    ```

### Finish WebAuthn Registration

*   **HTTP Method:** `POST`
*   **URL Path:** `/auth/register/webauthn/finish`
*   **Brief Description:** Finish WebAuthn registration by verifying the client's response.
*   **Expected Payload/Body:**
    ```json
    {
        "credential": { ... },
        "challenge": "string"
    }
    ```
*   **Expected Response:**
    ```json
    {
        "status": "ok"
    }
    ```

### Begin WebAuthn Authentication

*   **HTTP Method:** `POST`
*   **URL Path:** `/auth/login/webauthn/begin`
*   **Brief Description:** Begin WebAuthn authentication by generating a challenge.
*   **Expected Payload/Body:**
    ```json
    {
        "user_id": "integer"
    }
    ```
*   **Expected Response:**
    ```json
    {
        "challenge": "string",
        "options": { ... }
    }
    ```

### Finish WebAuthn Authentication

*   **HTTP Method:** `POST`
*   **URL Path:** `/auth/login/webauthn/finish`
*   **Brief Description:** Finish WebAuthn authentication by verifying the client's response.
*   **Expected Payload/Body:**
    ```json
    {
        "credential": { ... },
        "challenge": "string"
    }
    ```
*   **Expected Response:**
    ```json
    {
        "access_token": "string",
        "token_type": "bearer"
    }
    ```

## QR Code Login

### Start QR Login

*   **HTTP Method:** `POST`
*   **URL Path:** `/auth/qr-login/start`
*   **Brief Description:** Initiates a QR code login flow for a new device.
*   **Expected Response:** An image of a QR code.

### Approve QR Login

*   **HTTP Method:** `POST`
*   **URL Path:** `/auth/qr-login/approve`
*   **Brief Description:** Approves a QR code login request from an authenticated device.
*   **Expected Payload/Body:**
    ```json
    {
        "token": "string"
    }
    ```
*   **Expected Response:**
    ```json
    {
        "status": "success",
        "detail": "Login approved for the new device."
    }
    ```

### Poll QR Login Status

*   **HTTP Method:** `GET`
*   **URL Path:** `/auth/qr-login/poll/{token}`
*   **Brief Description:** Polls for the status of a QR code login request.
*   **Expected Response:**
    ```json
    {
        "status": "string (pending, approved, or expired)",
        "access_token": "string (if approved)"
    }
    ```

### Cleanup Expired Sessions

*   **HTTP Method:** `POST`
*   **URL Path:** `/auth/qr-login/cleanup`
*   **Brief Description:** Cleans up expired QR code login sessions from the database.
*   **Expected Response:**
    ```json
    {
        "status": "success",
        "detail": "Expired sessions cleaned up."
    }
    ```

## Recovery Codes

### Generate Recovery Codes

*   **HTTP Method:** `POST`
*   **URL Path:** `/auth/recovery/generate`
*   **Brief Description:** Generate a new set of recovery codes for the current user.
*   **Expected Response:**
    ```json
    {
        "codes": ["string"]
    }
    ```

### Recovery Login

*   **HTTP Method:** `POST`
*   **URL Path:** `/auth/recovery/login`
*   **Brief Description:** Log in using a one-time recovery code.
*   **Expected Payload/Body:**
    ```json
    {
        "email": "string",
        "code": "string"
    }
    ```
*   **Expected Response:**
    ```json
    {
        "access_token": "string",
        "token_type": "bearer"
    }
    ```

## User Management

### Get Current User

*   **HTTP Method:** `GET`
*   **URL Path:** `/users/me`
*   **Brief Description:** Get current logged-in user's information.
*   **Expected Response:**
    ```json
    {
        "id": "integer",
        "full_name": "string",
        "email": "string",
        "roll_number": "string",
        "role": "string",
        "is_active": "boolean",
        "is_superuser": "boolean",
        "school_class_id": "integer (optional)"
    }
    ```

## Admin User Management

### Create User

*   **HTTP Method:** `POST`
*   **URL Path:** `/admin/users/`
*   **Brief Description:** Create a new user.
*   **Expected Payload/Body:**
    ```json
    {
        "full_name": "string",
        "email": "string",
        "roll_number": "string",
        "password": "string",
        "role": "string",
        "is_active": "boolean",
        "is_superuser": "boolean",
        "school_class_id": "integer (optional)"
    }
    ```
*   **Expected Response:**
    ```json
    {
        "id": "integer",
        "full_name": "string",
        "email": "string",
        "roll_number": "string",
        "role": "string",
        "is_active": "boolean",
        "is_superuser": "boolean",
        "school_class_id": "integer (optional)"
    }
    ```

### Read Users

*   **HTTP Method:** `GET`
*   **URL Path:** `/admin/users/`
*   **Brief Description:** Retrieve users.
*   **Query Parameters:**
    *   `skip` (integer, optional)
    *   `limit` (integer, optional)
*   **Expected Response:**
    ```json
    [
        {
            "id": "integer",
            "full_name": "string",
            "email": "string",
            "roll_number": "string",
            "role": "string",
            "is_active": "boolean",
            "is_superuser": "boolean",
            "school_class_id": "integer (optional)"
        }
    ]
    ```

### Get User by Roll Number

*   **HTTP Method:** `GET`
*   **URL Path:** `/admin/users/{user_roll_number}`
*   **Brief Description:** Get a user by roll number.
*   **Expected Response:**
    ```json
    {
        "id": "integer",
        "full_name": "string",
        "email": "string",
        "roll_number": "string",
        "role": "string",
        "is_active": "boolean",
        "is_superuser": "boolean",
        "school_class_id": "integer (optional)"
    }
    ```

### Update User

*   **HTTP Method:** `PUT`
*   **URL Path:** `/admin/users/{user_roll_number}`
*   **Brief Description:** Update a user.
*   **Expected Payload/Body:**
    ```json
    {
        "full_name": "string (optional)",
        "email": "string (optional)",
        "roll_number": "string (optional)",
        "password": "string (optional)",
        "role": "string (optional)",
        "is_active": "boolean (optional)",
        "is_superuser": "boolean (optional)",
        "school_class_id": "integer (optional)"
    }
    ```
*   **Expected Response:**
    ```json
    {
        "id": "integer",
        "full_name": "string",
        "email": "string",
        "roll_number": "string",
        "role": "string",
        "is_active": "boolean",
        "is_superuser": "boolean",
        "school_class_id": "integer (optional)"
    }
    ```

### Delete User

*   **HTTP Method:** `DELETE`
*   **URL Path:** `/admin/users/{user_roll_number}`
*   **Brief Description:** Delete a user.
*   **Expected Response:**
    ```json
    {
        "id": "integer",
        "full_name": "string",
        "email": "string",
        "roll_number": "string",
        "role": "string",
        "is_active": "boolean",
        "is_superuser": "boolean",
        "school_class_id": "integer (optional)"
    }
    ```