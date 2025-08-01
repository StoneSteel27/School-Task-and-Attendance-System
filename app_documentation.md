# App Folder Documentation

This document provides a high-level overview of the files and their functions within the `app` folder of the School Task and Attendance System.

## `app/main.py`

This is the main entry point of the FastAPI application.

- **`app = FastAPI(...)`**: Initializes the FastAPI application with a project name and OpenAPI URL.
- **`app.include_router(api_router_v1, ...)`**: Includes the main API router from `app.api.v1.api`.
- **`@app.get("/")`**: A root endpoint to confirm the application is running.
- **`@app.get("/health")`**: A health check endpoint.
- **`setup_logging()`**: Sets up application-wide logging.

---

## `app/core/`

This package contains the core logic of the application, such as configuration, security, and logging.

### `app/core/config.py`

This file manages the application's configuration using Pydantic's `BaseSettings`.

- **`class Settings(BaseSettings)`**: Defines the configuration variables for the application, such as project name, database URL, and JWT settings. It loads these settings from a `.env` file.
- **`get_settings()`**: A function to get the settings object, cached for efficiency.

### `app/core/logging_config.py`

This file sets up the logging configuration for the application.

- **`setup_logging()`**: Configures a logger that outputs to both the console and a rotating file (`app.log`). It also afigures the `uvicorn` loggers to use the same format.

### `app/core/security.py`

This file handles security-related functions, including password hashing and JWT token management.

- **`pwd_context`**: An instance of `CryptContext` for password hashing and verification.
- **`verify_password(plain_password, hashed_password)`**: Verifies a plain password against a hashed one.
- **`get_password_hash(password)`**: Hashes a plain password.
- **`create_access_token(data, expires_delta)`**: Creates a JWT access token.
- **`decode_token(token)`**: Decodes a JWT token and returns the payload.

---

## `app/db/`

This package is responsible for database connections and session management.

### `app/db/base.py`

This file imports all the SQLAlchemy models to make them available to the `Base` metadata. This is crucial for `SQLAlchemy` to know about all the tables.

### `app/db/base_class.py`

This file defines the base class for all SQLAlchemy models.

- **`class Base(DeclarativeBase)`**: The declarative base class that all models inherit from. It also defines a naming convention for database constraints.

### `app/db/session.py`

This file handles the database session.

- **`engine`**: The SQLAlchemy engine, created from the `DATABASE_URL` in the settings.
- **`SessionLocal`**: A sessionmaker for creating database sessions.
- **`get_db()`**: A dependency that provides a database session to the API endpoints.

---

## `app/models/`

This package contains all the SQLAlchemy ORM models, which define the database tables.

### `app/models/academic/`

- **`announcement.py`**: Defines the `Announcement` model.
- **`task.py`**: Defines the `Task` and `StudentTaskSubmission` models, along with the `TaskStatus` enum.

### `app/models/attendance/`

- **`student_attendance.py`**: Defines the `StudentAttendance` model and the `AttendanceSession` and `AttendanceStatus` enums.
- **`teacher_attendance.py`**: Defines the `TeacherAttendance` model.

### `app/models/auth/`

- **`user.py`**: Defines the `User` model, which is central to the application.
- **`recovery_code.py`**: Defines the `RecoveryCode` model for one-time login codes.
- **`qr_login_session.py`**: Defines the `QRLoginSession` model for QR code-based login.
- **`webauthn.py`**: Defines the `WebAuthnCredential` and `WebAuthnChallenge` models for WebAuthn authentication.

### `app/models/core/`

- **`school_class.py`**: Defines the `SchoolClass` model and the `teacher_class_association` table for the many-to-many relationship between teachers and classes.
- **`schedule.py`**: Defines the `ClassScheduleSlot` and `Holiday` models.

---

## `app/schemas/`

This package contains all the Pydantic schemas, which are used for data validation, serialization, and documentation.

### `app/schemas/academic/`

- **`announcement.py`**: Defines Pydantic schemas for creating, updating, and reading announcements.
- **`task.py`**: Defines Pydantic schemas for tasks and student task submissions.

### `app/schemas/attendance/`

- **`student_attendance.py`**: Defines schemas for student attendance, including submission payloads and response models.
- **`teacher_attendance.py`**: Defines schemas for teacher attendance.
- **`attendance.py`**: Defines a general `AttendanceRequest` schema.

### `app/schemas/auth/`

- **`user.py`**: Defines schemas for user creation, updates, and responses.
- **`recovery_code.py`**: Defines schemas for recovery code generation and login.
- **`qr_login.py`**: Defines schemas for the QR code login flow.
- **`qr_login_session.py`**: Defines schemas for QR login sessions.
- **`token.py`**: Defines schemas for JWT tokens.
- **`webauthn.py`**: Defines schemas for the WebAuthn registration and authentication process.

### `app/schemas/core/`

- **`school_class.py`**: Defines schemas for school classes, including student and teacher assignments.
- **`schedule.py`**: Defines schemas for class schedules and holidays.
- **`subject.py`**: Defines a simple `Subject` schema.
- **`teacher_assigment.py`**: Defines schemas for teacher assignments.

---

## `app/crud/`

This package contains the CRUD (Create, Read, Update, Delete) operations for all the models.

### `app/crud/academic/`

- **`crud_announcement.py`**: CRUD functions for announcements.
- **`crud_student_task_submission.py`**: CRUD functions for student task submissions.
- **`crud_task.py`**: CRUD functions for tasks.

### `app/crud/attendance/`

- **`crud_student_attendance.py`**: CRUD functions for student attendance.
- **`crud_teacher_attendance.py`**: CRUD functions for teacher attendance.

### `app/crud/auth/`

- **`crud_user.py`**: CRUD functions for users, including student enrollment.
- **`crud_recovery_code.py`**: CRUD functions for recovery codes.
- **`crud_qr_login_session.py`**: CRUD functions for QR login sessions.
- **`crud_webauthn.py`**: CRUD functions for WebAuthn credentials and challenges.

### `app/crud/core/`

- **`crud_school_class.py`**: CRUD functions for school classes.
- **`crud_schedule.py`**: CRUD functions for schedules and holidays.
- **`crud_subject.py`**: CRUD functions for subjects.
- **`crud_teacher_assignment.py`**: CRUD functions for teacher assignments.

---

## `app/api/`

This package contains the API endpoints.

### `app/api/deps.py`

This file defines the FastAPI dependencies used across the application.

- **`get_db()`**: Provides a database session.
- **`get_current_user()`**: Gets the current user from a JWT token.
- **`get_current_active_user()`**: Ensures the current user is active.
- **`get_current_active_superuser()`**: Ensures the current user is a superuser.
- **`get_current_active_teacher()`**: Ensures the current user is a teacher.
- **Permission Dependencies**: `get_student_for_view_permission` and `get_teacher_for_view_permission` check for permissions before allowing access to user data.
- **Tool Managers**: Instantiates and provides managers for WebAuthn, QR codes, recovery codes, and geofencing.

### `app/api/v1/api.py`

This file aggregates all the API routers from the `endpoints` directory into a single `APIRouter`.

### `app/api/v1/endpoints/`

This package contains the API endpoints, organized by functionality.

#### `app/api/v1/endpoints/academic/`

- **`announcements_admin.py`**: Admin endpoints for managing announcements.
- **`submissions_teacher.py`**: Teacher endpoints for managing task submissions.
- **`tasks_announcements_teacher.py`**: Teacher endpoints for managing tasks and announcements.

#### `app/api/v1/endpoints/attendance/`

- **`attendance.py`**: Endpoints for teacher check-in and check-out.
- **`homeroom_attendance_teacher.py`**: Endpoints for homeroom teachers to submit and view student attendance.
- **`student_attendance_admin.py`**: Admin endpoints for viewing student attendance.

#### `app/api/v1/endpoints/auth/`

- **`auth.py`**: Endpoints for token-based login and WebAuthn registration/authentication.
- **`qr_login.py`**: Endpoints for the QR code login flow.
- **`recovery.py`**: Endpoints for generating and using recovery codes.
- **`users.py`**: Endpoint for the current user to get their own information.
- **`users_admin.py`**: Admin endpoints for managing users.

#### `app/api/v1/endpoints/core/`

- **`classes.py`**: General endpoints for managing school classes.
- **`classes_admin.py`**: Admin-specific endpoints for managing school classes.
- **`holidays.py`**: General endpoints for managing holidays.
- **`holidays_admin.py`**: Admin-specific endpoints for managing holidays.
- **`students.py`**: Endpoints for students to access their own data (schedule, attendance, tasks, etc.).
- **`students_teacher.py`**: Teacher endpoints for searching for students.
- **`teachers.py`**: Endpoints for teachers to access their own data (classes, schedule, tasks, etc.).

---
# Detailed Documentation

## `app/api/`

### `app/api/deps.py`

This file defines FastAPI dependencies that are used to provide resources and enforce authentication and authorization across the API endpoints.

-   **`get_db()`**: Provides a database session from the `SessionLocal` sessionmaker.
-   **`get_current_user()`**: Decodes the JWT token from the `Authorization` header to retrieve the current user.
-   **`get_current_active_user()`**: A dependency that ensures the user retrieved from the token is marked as active.
-   **`get_current_active_superuser()`**: A dependency that ensures the user is active and has superuser privileges.
-   **`get_current_active_teacher()`**: A dependency that ensures the user is active and has the "teacher" role.
-   **`get_student_for_view_permission()`**: A dependency that checks if the current user is authorized to view a student's data (either they are the student themselves or a superuser).
-   **`get_teacher_for_view_permission()`**: A dependency that checks if the current user is authorized to view a teacher's data (either they are the teacher themselves or a superuser).
-   **Tool Managers**:
    -   `get_webauthn_handler()`: Provides an instance of `WebAuthnHandler` for handling WebAuthn logic.
    -   `qr_code_manager`: An instance of `QRCodeManager` for generating QR codes.
    -   `recovery_codes_manager`: An instance of `RecoveryCodesManager` for handling recovery codes.
    -   `geofence_manager`: An instance of `GeofenceManager` for geofencing checks.
-   **`load_geofence_config()`**: Loads the geofence configuration from `geofence_config.json`.

### `app/api/v1/api.py`

This file acts as the main router for version 1 of the API. It includes all the individual endpoint routers from the `endpoints` directory and organizes them with prefixes and tags.

### `app/api/v1/endpoints/academic/`

This package contains endpoints related to academic activities like announcements and tasks.

-   **`announcements_admin.py`**:
    -   `create_announcement_by_admin`: Allows a superuser to create school-wide, class-specific, or subject-specific announcements.
    -   `get_all_announcements_by_admin`: Allows a superuser to retrieve all announcements with optional filters.
    -   `update_announcement_by_admin`: Allows a superuser to update an existing announcement.
    -   `delete_announcement_by_admin`: Allows a superuser to delete an announcement.
-   **`submissions_teacher.py`**:
    -   `list_task_submissions`: Allows a teacher to see all submissions for a specific task they created.
    -   `approve_submission`: Allows a teacher to approve a student's submission.
-   **`tasks_announcements_teacher.py`**:
    -   `create_task_for_class`: Allows a teacher to create a new task for a specific class and subject they are assigned to.
    -   `get_tasks_for_class_by_teacher`: Allows a teacher to retrieve tasks for a specific class they are assigned to.
    -   `update_task_by_teacher`: Allows a teacher to update a task they created.
    -   `delete_task_by_teacher`: Allows a teacher to delete a task they created.
    -   `create_announcement_by_teacher`: Allows a teacher to create a new announcement for a class they teach.
    -   `get_class_announcements_by_teacher`: Allows a teacher to retrieve class-specific announcements for a class they are assigned to.
    -   `update_announcement_by_teacher`: Allows a teacher to update an announcement they created.
    -   `delete_announcement_by_teacher`: Allows a teacher to delete an announcement they created.

### `app/api/v1/endpoints/attendance/`

This package contains endpoints for managing attendance.

-   **`attendance.py`**:
    -   `check_in`: Allows a teacher to check in, creating an attendance record.
    -   `check_out`: Allows a teacher to check out, updating the attendance record.
-   **`homeroom_attendance_teacher.py`**:
    -   `submit_homeroom_class_attendance`: Allows a homeroom teacher to submit attendance for their class.
    -   `get_homeroom_class_attendance_by_date_session`: Allows a homeroom teacher to get all attendance records for their class for a specific date and session.
-   **`student_attendance_admin.py`**:
    -   `admin_read_student_attendance_records`: Allows a superuser to retrieve attendance records for a specific student.
    -   `admin_read_classroom_attendance`: Allows a superuser to retrieve all attendance records for a specific classroom, date, and session.
    -   `admin_read_classroom_attendance_summary`: Allows a superuser to retrieve a summary of attendance percentages for a classroom.

### `app/api/v1/endpoints/auth/`

This package contains endpoints for authentication and user management.

-   **`auth.py`**:
    -   `login_for_access_token`: Standard OAuth2 password flow for token-based login.
    -   `webauthn_registration_begin`: Begins the WebAuthn registration process.
    -   `webauthn_registration_finish`: Finishes the WebAuthn registration process.
    -   `webauthn_authentication_begin`: Begins the WebAuthn authentication process.
    -   `webauthn_authentication_finish`: Finishes the WebAuthn authentication process.
-   **`qr_login.py`**:
    -   `qr_login_start`: Initiates a QR code login flow.
    -   `qr_login_approve`: Approves a QR code login request.
    -   `qr_login_poll`: Polls for the status of a QR code login request.
    -   `qr_login_cleanup`: Cleans up expired QR code login sessions.
-   **`recovery.py`**:
    -   `generate_recovery_codes`: Generates a new set of recovery codes for the current user.
    -   `recovery_login`: Logs in a user with a one-time recovery code.
-   **`users.py`**:
    -   `read_users_me`: Gets the current logged-in user's information.
-   **`users_admin.py`**:
    -   `create_user_endpoint`: Allows a superuser to create a new user.
    -   `read_users`: Allows a superuser to retrieve a list of users.
    -   `get_user_by_roll_number`: Allows a superuser to get a user by their roll number.
    -   `update_user_endpoint`: Allows a superuser to update a user.
    -   `delete_user_endpoint`: Allows a superuser to delete a user.

### `app/api/v1/endpoints/core/`

This package contains endpoints for managing the core structure of the school, such as classes and holidays.

-   **`classes.py`**:
    -   Contains endpoints for creating, reading, updating, and deleting school classes, as well as managing student and teacher assignments to classes.
-   **`classes_admin.py`**:
    -   Contains admin-specific endpoints for managing school classes, including bulk operations for assigning and unassigning students and teachers.
-   **`holidays.py`**:
    -   Contains endpoints for creating, reading, updating, and deleting holidays.
-   **`holidays_admin.py`**:
    -   Contains admin-specific endpoints for managing holidays, including bulk creation.
-   **`students.py`**:
    -   Contains endpoints for students to retrieve their own data, such as their schedule, attendance records, tasks, announcements, and subjects. It also includes an endpoint for submitting tasks.
-   **`students_teacher.py`**:
    -   `search_students`: Allows a teacher to search for students in the classes they teach.
-   **`teachers.py`**:
    -   Contains endpoints for teachers to retrieve their own data, such as their assigned classes, teaching load, schedule, and created tasks. It also includes endpoints for managing task submissions.

## `app/crud/`

This package contains the CRUD (Create, Read, Update, Delete) operations that interact directly with the database.

### `app/crud/academic/`

-   **`crud_announcement.py`**: Provides functions to get, create, update, and delete announcements. It includes functions to retrieve announcements based on different criteria like school-wide, class-specific, or subject-specific.
-   **`crud_student_task_submission.py`**: Provides functions to get, create, and approve student task submissions.
-   **`crud_task.py`**: Provides functions to get, create, update, and delete tasks. It also includes functions to retrieve tasks for a specific class or created by a specific teacher, and to create or update a student's task submission.

### `app/crud/attendance/`

-   **`crud_student_attendance.py`**: Provides functions for managing student attendance records, including creating records in bulk for a class, and retrieving attendance data for a student or a class. It also includes a function to calculate an attendance summary for a class.
-   **`crud_teacher_attendance.py`**: Provides functions for managing teacher attendance, including creating a check-in record and updating it with a check-out time.

### `app/crud/auth/`

-   **`crud_user.py`**: Provides functions for managing users, including creating, reading, updating, and deleting users. It also contains functions for assigning and unassigning students to and from classes, both individually and in bulk.
-   **`crud_recovery_code.py`**: Provides functions for creating and retrieving recovery codes.
-   **`crud_qr_login_session.py`**: Provides functions for managing QR login sessions, including creating, retrieving, updating, and cleaning up expired sessions.
-   **`crud_webauthn.py`**: Provides functions for managing WebAuthn credentials and challenges.

### `app/crud/core/`

-   **`crud_school_class.py`**: Provides functions for managing school classes, including creating, reading, updating, and deleting them.
-   **`crud_schedule.py`**: Provides functions for managing class schedules and holidays, including replacing a class's schedule, and creating, reading, updating, and deleting holidays.
-   **`crud_subject.py`**: Provides a function to get the subjects taught in a specific class.
-   **`crud_teacher_assignment.py`**: Provides functions for managing the assignment of teachers to classes and subjects.

## `app/models/`

This package contains the SQLAlchemy ORM models that define the structure of the database tables.

### `app/models/academic/`

-   **`announcement.py`**: Defines the `Announcement` model with fields like `title`, `content`, `attachment_url`, and relationships to the `User` and `SchoolClass` models.
-   **`task.py`**: Defines the `Task` and `StudentTaskSubmission` models. `Task` represents an assignment given by a teacher, while `StudentTaskSubmission` tracks each student's submission for a task. It also defines the `TaskStatus` enum (`PENDING`, `SUBMITTED`, `APPROVED`).

### `app/models/attendance/`

-   **`student_attendance.py`**: Defines the `StudentAttendance` model, which records the attendance of a student for a specific date and session. It includes the `AttendanceSession` (`MORNING`, `AFTERNOON`) and `AttendanceStatus` (`PRESENT`, `ABSENT`) enums.
-   **`teacher_attendance.py`**: Defines the `TeacherAttendance` model, which records the check-in and check-out times of a teacher.

### `app/models/auth/`

-   **`user.py`**: Defines the `User` model, which is the central model for all users in the system (students, teachers, and principals). It contains fields like `roll_number`, `email`, `hashed_password`, `role`, and relationships to other models like `SchoolClass`, `StudentAttendance`, `Task`, and `Announcement`.
-   **`recovery_code.py`**: Defines the `RecoveryCode` model for storing hashed one-time recovery codes for users.
-   **`qr_login_session.py`**: Defines the `QRLoginSession` model for managing the state of QR code-based login attempts.
-   **`webauthn.py`**: Defines the `WebAuthnCredential` and `WebAuthnChallenge` models for storing WebAuthn credentials and challenges for passwordless authentication.

### `app/models/core/`

-   **`school_class.py`**: Defines the `SchoolClass` model, which represents a class in the school. It includes relationships to students and teachers. It also defines the `teacher_class_association` table, which is a many-to-many relationship between teachers and classes, allowing a teacher to be assigned to multiple classes and a class to have multiple teachers.
-   **`schedule.py`**: Defines the `ClassScheduleSlot` model, which represents a single period in a class's schedule, and the `Holiday` model, which represents a holiday.

## `app/schemas/`

This package contains the Pydantic schemas that are used for data validation, serialization, and generating OpenAPI documentation.

### `app/schemas/academic/`

-   **`announcement.py`**: Defines schemas for creating, updating, and reading announcements (`AnnouncementCreate`, `AnnouncementUpdate`, `Announcement`).
-   **`task.py`**: Defines schemas for tasks and student task submissions (`TaskCreate`, `TaskUpdate`, `Task`, `StudentTaskSubmissionCreate`, `StudentTaskSubmissionUpdate`, `StudentTaskSubmission`, `TaskWithSubmissionStatus`).

### `app/schemas/attendance/`

-   **`student_attendance.py`**: Defines schemas for student attendance, including `StudentAttendanceEntryInput` for submitting attendance, `ClassAttendanceSubmission` for the submission payload, and various response schemas.
-   **`teacher_attendance.py`**: Defines schemas for teacher attendance (`TeacherAttendanceCreate`, `TeacherAttendanceUpdate`, `TeacherAttendanceInDB`).
-   **`attendance.py`**: Defines the `AttendanceRequest` schema, which is used for providing location data for attendance.

### `app/schemas/auth/`

-   **`user.py`**: Defines schemas for user management (`UserCreate`, `UserUpdate`, `User`).
-   **`recovery_code.py`**: Defines schemas for recovery code generation and login (`RecoveryCodeCreate`, `RecoveryCodeLoginRequest`, `RecoveryCodesResponse`).
-   **`qr_login.py`**: Defines schemas for the QR code login flow (`QRLoginApproveRequest`, `QRLoginPollResponse`).
-   **`qr_login_session.py`**: Defines schemas for QR login sessions (`QRLoginSessionCreate`, `QRLoginSessionUpdate`, `QRLoginSession`).
-   **`token.py`**: Defines schemas for JWT tokens (`Token`, `TokenData`).
-   **`webauthn.py`**: Defines schemas for the WebAuthn registration and authentication process.

### `app/schemas/core/`

-   **`school_class.py`**: Defines schemas for school classes, including schemas for managing student and teacher assignments (`SchoolClassCreate`, `SchoolClassUpdate`, `SchoolClass`, `BulkStudentRollNumbers`, `StudentAssignmentStatus`, `ClassTeacherAssignmentsCreate`, `ClassTeacherAssignmentsRemove`, `BatchAssignmentResult`).
-   **`schedule.py`**: Defines schemas for class schedules and holidays (`ClassScheduleSlotCreateInput`, `ClassScheduleSlotsBulkCreate`, `HolidayCreate`, `HolidayUpdate`, `Holiday`, `HolidayBulkCreate`).
-   **`subject.py`**: Defines a simple `Subject` schema.
-   **`teacher_assigment.py`**: Defines schemas for teacher assignments (`TeacherAssignmentCreate`, `TeacherAssignmentSubject`).