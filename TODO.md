# Project TODO List

This document tracks the necessary improvements and bug fixes for the School Task and Attendance System.
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
