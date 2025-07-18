# Project Test Suite TODO List

This document tracks the missing tests for the School Task and Attendance System, categorized by feature area.

## 1. Authentication (`test_auth.py`)

- **Critical:** The current test file only covers the standard password-based login. The following complex and security-sensitive authentication mechanisms are completely untested.

- **Missing Tests:**
    - **WebAuthn Registration:**
        - Test successful start of WebAuthn registration (`/register/webauthn/begin`).
        - Test successful completion of WebAuthn registration (`/register/webauthn/finish`).
        - Test failure when providing an invalid challenge.
        - Test failure when trying to register an already registered credential.
    - **WebAuthn Login:**
        - Test successful start of WebAuthn login (`/login/webauthn/begin`).
        - Test successful completion of WebAuthn login (`/login/webauthn/finish`) and token issuance.
        - Test failure with an invalid challenge.
        - Test failure with an unregistered user/credential.
    - **QR Code Login:**
        - Test successful initiation of a QR code session (`/qr-login/start`), verifying a QR code image is returned.
        - Test successful approval of a QR session (`/qr-login/approve`) by an authenticated user.
        - Test successful polling (`/qr-login/poll`) by the new device to get the access token.
        - Test polling status before and after approval.
        - Test failure for an expired QR session token.
        - Test failure when trying to approve a non-existent or invalid token.
    - **Recovery Code Login:**
        - Test successful generation of new recovery codes (`/recovery/generate`), ensuring old ones are invalidated.
        - Test successful login using a valid recovery code (`/recovery/login`).
        - Test that a recovery code is marked as used after a successful login.
        - Test failure when trying to log in with an already used recovery code.
        - Test failure when trying to log in with an invalid or non-existent code.

## 2. Student Features (New File: `test_students.py`)

- **Critical:** Core data retrieval endpoints for students are untested. The tests below cover both existing but untested endpoints and features that are planned in `TODO.md` but not yet implemented.

- **Missing Tests for Existing Endpoints:**
    - **Get Schedule (`/me/schedule`):**
        - Test successful retrieval of the weekly schedule.
        - Test successful retrieval of the schedule for a specific day.
        - Test that an empty list is returned for a holiday.
        - Test that a 404 is returned for a student not enrolled in a class.
    - **Get Attendance (`/me/attendance`):**
        - Test successful retrieval of attendance records within a date range.
        - Test with valid and invalid date formats.
        - Test that an empty list is returned for a range with no records.
    - **Get Tasks (`/me/tasks`):**
        - Test successful retrieval of all tasks for the student's class.
        - Test that an empty list is returned if there are no tasks.
    - **Get Announcements (`/me/announcements`):**
        - Test successful retrieval of a mix of school-wide, class, and subject announcements.
        - Test that the endpoint correctly deduplicates announcements.

- **Tests for New/Planned Features:**
    - **List Subjects (For New Endpoint):**
        - *Note: This feature must be implemented first (see `TODO.md`).*
        - Once created, test that a student gets the correct list of subjects for their class.
    - **Task Submission Status (For Enhanced Endpoint):**
        - *Note: This feature must be implemented first (see `TODO.md`).*
        - Once implemented, test that the response for `/me/tasks` includes the correct submission status (`pending`, `submitted`, `approved`).
    - **Announcement Attachments (For Enhanced Endpoint):**
        - *Note: This feature must be implemented first (see `TODO.md`).*
        - Once implemented, test that announcements in the API response contain a valid URL or identifier for their attachments.

## 3. Teacher Features (New File: `test_teacher_features.py` or similar)

- **Critical:** Key teacher functionalities like attendance and schedule are untested. The tests below cover both existing but untested endpoints and features that are planned in `TODO.md` but not yet implemented.

- **Missing Tests for Existing Endpoints:**
    - **Homeroom Attendance (`/homeroom/{class_code}/...`):**
        - Test successful submission of attendance for a full class.
        - Test successful retrieval of a previously submitted attendance record.
        - Test failure when a non-homeroom teacher tries to submit or view attendance.
        - Test failure when providing an invalid class code, date, or session.

- **Tests for New/Planned Features:**
    - **Teacher's Schedule (For New Endpoint):**
        - *Note: This feature must be implemented first (see `TODO.md`).*
        - Once the endpoint is created, add tests to verify a teacher can retrieve their own schedule.
    - **Student Search (For New Endpoint):**
        - *Note: This feature must be implemented first (see `TODO.md`).*
        - Once the endpoint is created, add tests to verify a teacher can search for students in their classes.
    - **Reviewing Submissions (For New Endpoints):**
        - *Note: This feature must be implemented first (see `TODO.md`).*
        - Once the endpoints are created, add tests to:
            - Verify a teacher can list all submissions for a task they created.
            - Verify a teacher can approve a submission and the status is updated.
            - Verify a teacher cannot view or approve submissions for a task they did not create.