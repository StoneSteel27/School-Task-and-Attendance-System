# Academic API Endpoints

## Admin Announcement Endpoints

### Create Announcement

*   **HTTP Method:** `POST`
*   **URL Path:** `/api/v1/admin/announcements/`
*   **Brief Description:** Admin: Create a new announcement (school-wide, class-specific, or subject-specific)
*   **Expected Payload/Body:**
    ```json
    {
        "title": "string",
        "content": "string",
        "is_school_wide": "boolean",
        "school_class_id": "integer (optional)",
        "subject": "string (optional)"
    }
    ```
*   **Expected Response:**
    ```json
    {
        "id": "integer",
        "title": "string",
        "content": "string",
        "is_school_wide": "boolean",
        "school_class_id": "integer (optional)",
        "subject": "string (optional)",
        "created_at": "datetime",
        "updated_at": "datetime",
        "created_by_user_id": "integer"
    }
    ```

### Get All Announcements

*   **HTTP Method:** `GET`
*   **URL Path:** `/api/v1/admin/announcements/`
*   **Brief Description:** Admin: Get all announcements (school-wide, class-specific, subject-specific)
*   **Query Parameters:**
    *   `is_school_wide` (boolean, optional)
    *   `class_code` (string, optional)
    *   `subject` (string, optional)
*   **Expected Response:**
    ```json
    [
        {
            "id": "integer",
            "title": "string",
            "content": "string",
            "is_school_wide": "boolean",
            "school_class_id": "integer (optional)",
            "subject": "string (optional)",
            "created_at": "datetime",
            "updated_at": "datetime",
            "created_by_user_id": "integer"
        }
    ]
    ```

### Update Announcement

*   **HTTP Method:** `PUT`
*   **URL Path:** `/api/v1/admin/announcements/{announcement_id}`
*   **Brief Description:** Admin: Update an existing announcement
*   **Expected Payload/Body:**
    ```json
    {
        "title": "string (optional)",
        "content": "string (optional)",
        "is_school_wide": "boolean (optional)",
        "school_class_id": "integer (optional)",
        "subject": "string (optional)"
    }
    ```
*   **Expected Response:**
    ```json
    {
        "id": "integer",
        "title": "string",
        "content": "string",
        "is_school_wide": "boolean",
        "school_class_id": "integer (optional)",
        "subject": "string (optional)",
        "created_at": "datetime",
        "updated_at": "datetime",
        "created_by_user_id": "integer"
    }
    ```

### Delete Announcement

*   **HTTP Method:** `DELETE`
*   **URL Path:** `/api/v1/admin/announcements/{announcement_id}`
*   **Brief Description:** Admin: Delete an announcement
*   **Expected Response:**
    ```json
    {
        "id": "integer",
        "title": "string",
        "content": "string",
        "is_school_wide": "boolean",
        "school_class_id": "integer (optional)",
        "subject": "string (optional)",
        "created_at": "datetime",
        "updated_at": "datetime",
        "created_by_user_id": "integer"
    }
    ```

## Teacher Submission Endpoints

### List Task Submissions

*   **HTTP Method:** `GET`
*   **URL Path:** `/api/v1/teachers/tasks/{task_id}/submissions`
*   **Brief Description:** Teacher: List submissions for a task
*   **Expected Response:**
    ```json
    [
        {
            "id": "integer",
            "task_id": "integer",
            "student_id": "integer",
            "submission_url": "string",
            "status": "string",
            "submitted_at": "datetime",
            "updated_at": "datetime"
        }
    ]
    ```

### Approve Submission

*   **HTTP Method:** `PUT`
*   **URL Path:** `/api/v1/teachers/submissions/{submission_id}/approve`
*   **Brief Description:** Teacher: Approve a submission
*   **Expected Response:**
    ```json
    {
        "id": "integer",
        "task_id": "integer",
        "student_id": "integer",
        "submission_url": "string",
        "status": "string",
        "submitted_at": "datetime",
        "updated_at": "datetime"
    }
    ```

## Teacher Task and Announcement Endpoints

### Create Task for Class

*   **HTTP Method:** `POST`
*   **URL Path:** `/api/v1/teachers/classes/{class_code}/tasks`
*   **Brief Description:** Teacher: Create a new task for a specific class and subject
*   **Expected Payload/Body:**
    ```json
    {
        "title": "string",
        "description": "string",
        "due_date": "date",
        "subject": "string"
    }
    ```
*   **Expected Response:**
    ```json
    {
        "id": "integer",
        "title": "string",
        "description": "string",
        "due_date": "date",
        "subject": "string",
        "school_class_id": "integer",
        "created_by_teacher_id": "integer",
        "created_at": "datetime",
        "updated_at": "datetime"
    }
    ```

### Get Tasks for Class

*   **HTTP Method:** `GET`
*   **URL Path:** `/api/v1/teachers/classes/{class_code}/tasks`
*   **Brief Description:** Teacher: Get all tasks for a specific class and optionally filter by subject
*   **Query Parameters:**
    *   `subject` (string, optional)
*   **Expected Response:**
    ```json
    [
        {
            "id": "integer",
            "title": "string",
            "description": "string",
            "due_date": "date",
            "subject": "string",
            "school_class_id": "integer",
            "created_by_teacher_id": "integer",
            "created_at": "datetime",
            "updated_at": "datetime"
        }
    ]
    ```

### Update Task

*   **HTTP Method:** `PUT`
*   **URL Path:** `/api/v1/teachers/tasks/{task_id}`
*   **Brief Description:** Teacher: Update an existing task
*   **Expected Payload/Body:**
    ```json
    {
        "title": "string (optional)",
        "description": "string (optional)",
        "due_date": "date (optional)",
        "subject": "string (optional)"
    }
    ```
*   **Expected Response:**
    ```json
    {
        "id": "integer",
        "title": "string",
        "description": "string",
        "due_date": "date",
        "subject": "string",
        "school_class_id": "integer",
        "created_by_teacher_id":. "integer",
        "created_at": "datetime",
        "updated_at": "datetime"
    }
    ```

### Delete Task

*   **HTTP Method:** `DELETE`
*   **URL Path:** `/api/v1/teachers/tasks/{task_id}`
*   **Brief Description:** Teacher: Delete a task
*   **Expected Response:**
    ```json
    {
        "id": "integer",
        "title": "string",
        "description": "string",
        "due_date": "date",
        "subject": "string",
        "school_class_id": "integer",
        "created_by_teacher_id": "integer",
        "created_at": "datetime",
        "updated_at": "datetime"
    }
    ```

### Create Announcement

*   **HTTP Method:** `POST`
*   **URL Path:** `/api/v1/teachers/announcements`
*   **Brief Description:** Teacher: Create a new announcement (class-specific or subject-specific)
*   **Expected Payload/Body:**
    ```json
    {
        "title": "string",
        "content": "string",
        "is_school_wide": "boolean",
        "school_class_id": "integer (optional)",
        "subject": "string (optional)"
    }
    ```
*   **Expected Response:**
    ```json
    {
        "id": "integer",
        "title": "string",
        "content": "string",
        "is_school_wide": "boolean",
        "school_class_id": "integer (optional)",
        "subject": "string (optional)",
        "created_at": "datetime",
        "updated_at": "datetime",
        "created_by_user_id": "integer"
    }
    ```

### Get Class Announcements

*   **HTTP Method:** `GET`
*   **URL Path:** `/api/v1/teachers/classes/{class_code}/announcements`
*   **Brief Description:** Teacher: Get class-specific announcements, optionally filtered by subject
*   **Query Parameters:**
    *   `subject` (string, optional)
*   **Expected Response:**
    ```json
    [
        {
            "id": "integer",
            "title": "string",
            "content": "string",
            "is_school_wide": "boolean",
            "school_class_id": "integer (optional)",
            "subject": "string (optional)",
            "created_at": "datetime",
            "updated_at": "datetime",
            "created_by_user_id": "integer"
        }
    ]
    ```

### Update Announcement

*   **HTTP Method:** `PUT`
*   **URL Path:** `/api/v1/teachers/announcements/{announcement_id}`
*   **Brief Description:** Teacher: Update an existing announcement
*   **Expected Payload/Body:**
    ```json
    {
        "title": "string (optional)",
        "content": "string (optional)",
        "is_school_wide": "boolean (optional)",
        "school_class_id": "integer (optional)",
        "subject": "string (optional)"
    }
    ```
*   **Expected Response:**
    ```json
    {
        "id": "integer",
        "title": "string",
        "content": "string",
        "is_school_wide": "boolean",
        "school_class_id": "integer (optional)",
        "subject": "string (optional)",
        "created_at": "datetime",
        "updated_at": "datetime",
        "created_by_user_id": "integer"
    }
    ```

### Delete Announcement

*   **HTTP Method:** `DELETE`
*   **URL Path:** `/api/v1/teachers/announcements/{announcement_id}`
*   **Brief Description:** Teacher: Delete an announcement
*   **Expected Response:**
    ```json
    {
        "id": "integer",
        "title": "string",
        "content": "string",
        "is_school_wide": "boolean",
        "school_class_id": "integer (optional)",
        "subject": "string (optional)",
        "created_at": "datetime",
        "updated_at": "datetime",
        "created_by_user_id": "integer"
    }
    ```

### Get My Subjects

*   **HTTP Method:** `GET`
*   **URL Path:** `/api/v1/teachers/my-subjects`
*   **Brief Description:** Teacher: Get all subjects taught by the current teacher
*   **Expected Response:**
    ```json
    [
        {
            "school_class_id": "integer",
            "school_class_name": "string",
            "school_class_code": "string",
            "subjects": ["string"]
        }
    ]
    ```