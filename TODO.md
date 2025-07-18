# Project TODO List

This document tracks the necessary improvements and bug fixes for the School Task and Attendance System.

## High Priority - Core Functionality

### 1. Refactor WebAuthn Implementation to Use Database

- **Issue:** The current WebAuthn implementation in `attendance_system_tools/webauthn_handler.py` uses a temporary, in-memory dictionary (`TEMP_USER_CREDENTIALS_STORE`) to store user credential data. This data is lost every time the application restarts, making the feature non-functional for persistent use.
- **Required Fix:**
    1.  **Create a Database Model:** Define a new SQLAlchemy model `WebAuthnCredential` to store credential information (e.g., `user_id`, `credential_id`, `public_key`, `sign_count`).
    2.  **Create CRUD Functions:** Implement Create, Read, Update, and Delete functions for the `WebAuthnCredential` model.
    3.  **Refactor `WebAuthnHandler`:** Modify the `WebAuthnHandler` class to replace all interactions with `TEMP_USER_CREDENTIALS_STORE` with calls to the new CRUD functions, persisting data in the database.
    4.  **Refactor Challenge Storage:** Replace the `TEMP_CHALLENGE_STORE` with a database-backed solution to persist challenges across requests.

### 2. Refactor QR Code Login to Use Database

- **Issue:** The QR code login flow in `app/api/v1/endpoints/qr_login.py` relies on an in-memory dictionary (`QR_LOGIN_SESSIONS`) to manage the state of login attempts. This is not a persistent storage solution.
- **Required Fix:**
    1.  **Create a Database Model:** Define a new SQLAlchemy model `QRLoginSession` to store session data (e.g., `token`, `status`, `user_id`, `created_at`).
    2.  **Create CRUD Functions:** Implement functions to create, retrieve, and update `QRLoginSession` records in the database.
    3.  **Refactor QR Login Endpoints:** Modify the `/qr-login/start`, `/qr-login/approve`, and `/qr-login/poll` endpoints to use the database for managing session state instead of the in-memory dictionary.
    4.  **Implement a Cleanup Mechanism:** Add a scheduled task or a background process to periodically delete expired QR login sessions from the database.

---

## Teacher Features

### 1. Implement Teacher Schedule Endpoint

- **Issue:** There is no endpoint for a teacher to view their own daily or weekly class schedule.
- **Required Fix:**
    1.  **Create an Endpoint:** Add a new endpoint, such as `/api/v1/teachers/me/schedule`.
    2.  **Implement Logic:** This endpoint should query the `ClassScheduleSlot` model, filtering for slots where the `teacher_id` matches the current user's ID.
    3.  **Reuse Schema:** The existing `schemas.ClassScheduleSlot` can likely be reused for the response.

### 2. Implement Student Search for Teachers

- **Issue:** Teachers need the ability to search for students and view their details, but no such endpoint exists.
- **Required Fix:**
    1.  **Create an Endpoint:** Add a new endpoint, e.g., `/api/v1/teachers/students/search`.
    2.  **Implement Search Logic:** The endpoint should allow searching for students by name, roll number, or class. It should only return students that the teacher is authorized to see (e.g., students in their classes).
    3.  **Define Response Schema:** Create a Pydantic schema for the student details to be returned in the search results.

### 3. Implement Task Submission Review for Teachers

- **Issue:** Teachers can create tasks, but they cannot view student submissions, grade them, or approve them.
- **Required Fix:**
    1.  **Create Endpoints:**
        -   `GET /api/v1/tasks/{task_id}/submissions`: To list all submissions for a specific task.
        -   `PUT /api/v1/submissions/{submission_id}/approve`: To mark a submission as "approved".
    2.  **Implement Logic:** The endpoints must verify that the teacher is authorized to manage the task and its submissions.
    3.  **Update Schemas:** Create or update schemas to handle the submission data and the approval status change.

---

## Student Features

### 1. Implement "List Subjects" Endpoint

- **Issue:** The application is missing a dedicated endpoint for students to view a simple list of their subjects, a feature specified in the project requirements.
- **Required Fix:**
    1.  **Create an Endpoint:** Add a new endpoint, such as `/api/v1/students/me/subjects`.
    2.  **Implement Logic:** The endpoint should retrieve the subjects associated with the student's enrolled class from the database.
    3.  **Define Schema:** Create a Pydantic schema to represent a subject for the API response.

### 2. Expose Task Submission Status to Students

- **Issue:** While students can submit tasks, they cannot view the current status of their submissions (e.g., `pending`, `submitted`, `approved`).
- **Required Fix:**
    1.  **Enhance Task Endpoints:** Modify the existing `/me/tasks` endpoint or create a new one (e.g., `/me/submissions`) to include the submission status for each task.
    2.  **Update Schemas:** Adjust the Pydantic schemas to include the `submission_status` field in the response.

### 3. Clarify and Implement Announcement Attachments

- **Issue:** The functionality for handling and delivering announcement attachments is not fully implemented or clear.
- **Required Fix:**
    1.  **Investigate Current State:** Review the `Announcement` model, schema, and CRUD functions to determine how attachments are currently handled.
    2.  **Implement File Handling:** If necessary, add logic to upload, store, and serve attachment files.
    3.  **Update API Response:** Ensure the announcement-related API endpoints include a URL or other identifier for accessing the attachment.
