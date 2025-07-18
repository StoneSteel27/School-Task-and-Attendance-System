# Project TODO List

This document tracks the necessary improvements and bug fixes for the School Task and Attendance System.

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
