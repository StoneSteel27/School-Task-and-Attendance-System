# Core API Endpoints

## School Class Management

### Create School Class

*   **HTTP Method:** `POST`
*   **URL Path:** `/api/v1/classes/`
*   **Brief Description:** Create a new school class.
*   **Expected Payload/Body:**
    ```json
    {
        "name": "string",
        "class_code": "string",
        "grade": "integer",
        "homeroom_teacher_id": "integer (optional)"
    }
    ```
*   **Expected Response:**
    ```json
    {
        "id": "integer",
        "name": "string",
        "class_code": "string",
        "grade": "integer",
        "homeroom_teacher_id": "integer (optional)",
        "students": [],
        "teaching_staff": []
    }
    ```

### Read School Class

*   **HTTP Method:** `GET`
*   **URL Path:** `/api/v1/classes/{class_code}`
*   **Brief Description:** Get a specific school class by its class_code.
*   **Expected Response:**
    ```json
    {
        "id": "integer",
        "name": "string",
        "class_code": "string",
        "grade": "integer",
        "homeroom_teacher_id": "integer (optional)",
        "students": [ ... ],
        "teaching_staff": [ ... ]
    }
    ```

### Read School Classes

*   **HTTP Method:** `GET`
*   **URL Path:** `/api/v1/classes/`
*   **Brief Description:** Retrieve all school classes.
*   **Query Parameters:**
    *   `skip` (integer, optional)
    *   `limit` (integer, optional)
*   **Expected Response:**
    ```json
    [
        {
            "id": "integer",
            "name": "string",
            "class_code": "string",
            "grade": "integer",
            "homeroom_teacher_id": "integer (optional)",
            "students": [ ... ],
            "teaching_staff": [ ... ]
        }
    ]
    ```

### Update School Class

*   **HTTP Method:** `PUT`
*   **URL Path:** `/api/v1/classes/{class_code}`
*   **Brief Description:** Update the details of an existing school class.
*   **Expected Payload/Body:**
    ```json
    {
        "name": "string (optional)",
        "class_code": "string (optional)",
        "grade": "integer (optional)",
        "homeroom_teacher_id": "integer (optional)"
    }
    ```
*   **Expected Response:**
    ```json
    {
        "id": "integer",
        "name": "string",
        "class_code": "string",
        "grade": "integer",
        "homeroom_teacher_id": "integer (optional)",
        "students": [ ... ],
        "teaching_staff": [ ... ]
    }
    ```

### Delete School Class

*   **HTTP Method:** `DELETE`
*   **URL Path:** `/api/v1/classes/{class_code}`
*   **Brief Description:** Delete a school class by its class_code.
*   **Expected Response:**
    ```json
    {
        "id": "integer",
        "name": "string",
        "class_code": "string",
        "grade": "integer",
        "homeroom_teacher_id": "integer (optional)",
        "students": [ ... ],
        "teaching_staff": [ ... ]
    }
    ```

### Get Class Teaching Staff

*   **HTTP Method:** `GET`
*   **URL Path:** `/api/v1/classes/{class_code}/teaching-staff`
*   **Brief Description:** Get the list of teachers and the subjects they teach for a specific class.
*   **Expected Response:**
    ```json
    [
        {
            "teacher_id": "integer",
            "teacher_name": "string",
            "subject": "string"
        }
    ]
    ```

### Get Class Schedule

*   **HTTP Method:** `GET`
*   **URL Path:** `/api/v1/classes/{class_code}/schedule`
*   **Brief Description:** Get the schedule for a specific school class.
*   **Query Parameters:**
    *   `target_date` (date, optional)
*   **Expected Response:**
    ```json
    [
        {
            "id": "integer",
            "day_of_week": "integer",
            "start_time": "time",
            "end_time": "time",
            "subject": "string",
            "teacher_id": "integer",
            "school_class_id": "integer"
        }
    ]
    ```

### Replace Class Schedule

*   **HTTP Method:** `PUT`
*   **URL Path:** `/api/v1/classes/{class_code}/schedule`
*   **Brief Description:** Replace the entire schedule for a class on a specific date.
*   **Expected Payload/Body:**
    ```json
    [
        {
            "day_of_week": "integer",
            "start_time": "time",
            "end_time": "time",
            "subject": "string",
            "teacher_id": "integer"
        }
    ]
    ```
*   **Expected Response:**
    ```json
    [
        {
            "id": "integer",
            "day_of_week": "integer",
            "start_time": "time",
            "end_time": "time",
            "subject": "string",
            "teacher_id": "integer",
            "school_class_id": "integer"
        }
    ]
    ```

### Assign Multiple Students to a Class

*   **HTTP Method:** `POST`
*   **URL Path:** `/api/v1/classes/{class_code}/students`
*   **Brief Description:** Assign multiple students to a class by their roll numbers.
*   **Expected Payload/Body:**
    ```json
    {
        "roll_numbers": ["string"]
    }
    ```
*   **Expected Response:**
    ```json
    [
        {
            "roll_number": "string",
            "status": "string",
            "detail": "string"
        }
    ]
    ```

### Unassign Multiple Students from a Class

*   **HTTP Method:** `DELETE`
*   **URL Path:** `/api/v1/classes/{class_code}/students`
*   **Brief Description:** Unassign multiple students from a class by their roll numbers.
*   **Expected Payload/Body:**
    ```json
    {
        "roll_numbers": ["string"]
    }
    ```
*   **Expected Response:**
    ```json
    [
        {
            "roll_number": "string",
            "status": "string",
            "detail": "string"
        }
    ]
    ```

### Assign Multiple Teachers to Subjects in a Class

*   **HTTP Method:** `POST`
*   **URL Path:** `/api/v1/classes/{class_code}/teachers`
*   **Brief Description:** Assign multiple teachers to subjects in a class.
*   **Expected Payload/Body:**
    ```json
    [
        {
            "teacher_id": "integer",
            "subject": "string"
        }
    ]
    ```
*   **Expected Response:**
    ```json
    [
        {
            "teacher_id": "integer",
            "subject": "string",
            "status": "string",
            "detail": "string"
        }
    ]
    ```

### Unassign Multiple Teachers from Subjects in a Class

*   **HTTP Method:** `DELETE`
*   **URL Path:** `/api/v1/classes/{class_code}/teachers`
*   **Brief Description:** Unassign multiple teachers from subjects in a class.
*   **Expected Payload/Body:**
    ```json
    [
        {
            "teacher_id": "integer",
            "subject": "string"
        }
    ]
    ```
*   **Expected Response:**
    ```json
    [
        {
            "teacher_id": "integer",
            "subject": "string",
            "status": "string",
            "detail": "string"
        }
    ]
    ```

## Holiday Management

### Read Holidays

*   **HTTP Method:** `GET`
*   **URL Path:** `/api/v1/holidays/`
*   **Brief Description:** Retrieve holidays.
*   **Query Parameters:**
    *   `skip` (integer, optional)
    *   `limit` (integer, optional)
*   **Expected Response:**
    ```json
    [
        {
            "id": "integer",
            "name": "string",
            "start_date": "date",
            "end_date": "date",
            "grades": ["integer"]
        }
    ]
    ```

### Create Holiday

*   **HTTP Method:** `POST`
*   **URL Path:** `/api/v1/holidays/`
*   **Brief Description:** Create new holiday.
*   **Expected Payload/Body:**
    ```json
    {
        "name": "string",
        "start_date": "date",
        "end_date": "date",
        "grades": ["integer"]
    }
    ```
*   **Expected Response:**
    ```json
    {
        "id": "integer",
        "name": "string",
        "start_date": "date",
        "end_date": "date",
        "grades": ["integer"]
    }
    ```

### Update Holiday

*   **HTTP Method:** `PUT`
*   **URL Path:** `/api/v1/holidays/{holiday_id}`
*   **Brief Description:** Update a holiday.
*   **Expected Payload/Body:**
    ```json
    {
        "name": "string (optional)",
        "start_date": "date (optional)",
        "end_date": "date (optional)",
        "grades": ["integer (optional)"]
    }
    ```
*   **Expected Response:**
    ```json
    {
        "id": "integer",
        "name": "string",
        "start_date": "date",
        "end_date": "date",
        "grades": ["integer"]
    }
    ```

### Delete Holiday

*   **HTTP Method:** `DELETE`
*   **URL Path:** `/api/v1/holidays/{holiday_id}`
*   **Brief Description:** Delete a holiday.
*   **Expected Response:**
    ```json
    {
        "id": "integer",
        "name": "string",
        "start_date": "date",
        "end_date": "date",
        "grades": ["integer"]
    }
    ```

## Student Endpoints

### Get Student's Class Schedule

*   **HTTP Method:** `GET`
*   **URL Path:** `/api/v1/students/me/schedule`
*   **Brief Description:** Get Student's Class Schedule
*   **Query Parameters:**
    *   `target_date` (date, optional)
*   **Expected Response:**
    ```json
    [
        {
            "id": "integer",
            "day_of_week": "integer",
            "start_time": "time",
            "end_time": "time",
            "subject": "string",
            "teacher_id": "integer",
            "school_class_id": "integer"
        }
    ]
    ```

### Get Student's Attendance Records

*   **HTTP Method:** `GET`
*   **URL Path:** `/api/v1/students/me/attendance`
*   **Brief Description:** Get Student's Attendance Records over a Date Range
*   **Query Parameters:**
    *   `startDate` (string, YYYY-MM-DD)
    *   `endDate` (string, YYYY-MM-DD)
    *   `skip` (integer, optional)
    *   `limit` (integer, optional)
*   **Expected Response:**
    ```json
    [
        {
            "id": "integer",
            "student_id": "integer",
            "school_class_id": "integer",
            "teacher_id": "integer",
            "attendance_date": "date",
            "session": "string",
            "status": "string",
            "created_at": "datetime",
            "updated_at": "datetime"
        }
    ]
    ```

### Get Student's Tasks

*   **HTTP Method:** `GET`
*   **URL Path:** `/api/v1/students/me/tasks`
*   **Brief Description:** Get Student's Tasks
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
            "updated_at": "datetime",
            "submission_status": "string"
        }
    ]
    ```

### Get Student's Announcements

*   **HTTP Method:** `GET`
*   **URL Path:** `/api/v1/students/me/announcements`
*   **Brief Description:** Get Student's Announcements (School-wide, Class-specific, Subject-specific)
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

### Submit Task File

*   **HTTP Method:** `POST`
*   **URL Path:** `/api/v1/students/me/tasks/{task_id}/submit`
*   **Brief Description:** Submit a file for a student's task
*   **Expected Payload/Body (form-data):**
    *   `file`: The file to upload.
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

### List Student Subjects

*   **HTTP Method:** `GET`
*   **URL Path:** `/api/v1/students/me/subjects`
*   **Brief Description:** Get a list of subjects for the current student's class.
*   **Expected Response:**
    ```json
    [
        {
            "id": "integer",
            "name": "string"
        }
    ]
    ```

## Teacher Endpoints

### Search Students

*   **HTTP Method:** `GET`
*   **URL Path:** `/api/v1/teachers/search`
*   **Brief Description:** Search for students.
*   **Query Parameters:**
    *   `name` (string, optional)
    *   `roll_number` (string, optional)
    *   `class_code` (string, optional)
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

### Get My Classes

*   **HTTP Method:** `GET`
*   **URL Path:** `/api/v1/teachers/me/classes`
*   **Brief Description:** Get the list of classes that the current teacher is assigned to.
*   **Expected Response:**
    ```json
    [
        {
            "teacher_id": "integer",
            "teacher_name": "string",
            "subject": "string"
        }
    ]
    ```

### Get Teacher's Teaching Load

*   **HTTP Method:** `GET`
*   **URL Path:** `/api/v1/teachers/{teacher_roll_number}/teaching-load`
*   **Brief Description:** Get the list of classes and subjects a specific teacher is assigned to teach.
*   **Expected Response:**
    ```json
    [
        {
            "school_class_id": "integer",
            "school_class_name": "string",
            "school_class_code": "string",
            "subject": "string"
        }
    ]
    ```

### Get Teacher's Schedule

*   **HTTP Method:** `GET`
*   **URL Path:** `/api/v1/teachers/me/schedule`
*   **Brief Description:** Get Current Teacher's Schedule
*   **Query Parameters:**
    *   `target_date` (date, optional)
    *   `day_of_week` (integer, optional)
*   **Expected Response:**
    ```json
    [
        {
            "id": "integer",
            "day_of_week": "integer",
            "start_time": "time",
            "end_time": "time",
            "subject": "string",
            "teacher_id": "integer",
            "school_class_id": "integer"
        }
    ]
    ```

### Get Tasks Created by Me

*   **HTTP Method:** `GET`
*   **URL Path:** `/api/v1/teachers/me/tasks`
*   **Brief Description:** Get the list of tasks created by the current teacher.
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

### Create Announcement for My Class

*   **HTTP Method:** `POST`
*   **URL Path:** `/api/v1/teachers/me/announcements`
*   **Brief Description:** Create a new announcement for the class(es) you are teaching.
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

### Get Submissions for a Task

*   **HTTP Method:** `GET`
*   **URL Path:** `/api/v1/teachers/me/tasks/{task_id}/submissions`
*   **Brief Description:** Get all submissions for a specific task that you have created.
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

### Approve a Task Submission

*   **HTTP Method:** `PUT`
*   **URL Path:** `/api/v1/teachers/me/submissions/{submission_id}/approve`
*   **Brief Description:** Approve a task submission from a student.
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

### Get Announcements Created by Me

*   **HTTP Method:** `GET`
*   **URL Path:** `/api/v1/teachers/me/announcements`
*   **Brief Description:** Get the list of announcements created by the current teacher.
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