# Attendance API Endpoints

## Teacher Attendance

### Check-in

*   **HTTP Method:** `POST`
*   **URL Path:** `/api/v1/attendance/check-in`
*   **Brief Description:** Check in the current teacher, verifying their location and creating an attendance record.
*   **Expected Payload/Body:**
    ```json
    {
        "latitude": "float",
        "longitude": "float"
    }
    ```
*   **Expected Response:**
    ```json
    {
        "id": "integer",
        "teacher_id": "integer",
        "check_in_time": "datetime",
        "check_out_time": "datetime (optional)"
    }
    ```

### Check-out

*   **HTTP Method:** `POST`
*   **URL Path:** `/api/v1/attendance/check-out`
*   **Brief Description:** Check out the current teacher, verifying their location and updating the attendance record.
*   **Expected Payload/Body:**
    ```json
    {
        "latitude": "float",
        "longitude": "float"
    }
    ```
*   **Expected Response:**
    ```json
    {
        "id": "integer",
        "teacher_id": "integer",
        "check_in_time": "datetime",
        "check_out_time": "datetime"
    }
    ```

## Homeroom Teacher Attendance

### Submit Homeroom Class Attendance

*   **HTTP Method:** `POST`
*   **URL Path:** `/api/v1/teachers/homeroom-attendance/{class_code}/submit`
*   **Brief Description:** Submit attendance for all students in a specific homeroom class for a given date and session.
*   **Expected Payload/Body:**
    ```json
    {
        "attendance_date": "date",
        "session": "string (MORNING or AFTERNOON)",
        "entries": [
            {
                "student_roll_number": "string",
                "status": "string (PRESENT, ABSENT, LATE, EXCUSED)"
            }
        ]
    }
    ```
*   **Expected Response:**
    ```json
    {
        "school_class_id": "integer",
        "school_class_code": "string",
        "attendance_date": "date",
        "session": "string",
        "marked_by_teacher_id": "integer",
        "marked_by_teacher_name": "string",
        "total_students_in_payload": "integer",
        "successful_records": "integer",
        "failed_records": "integer",
        "results": [
            {
                "student_roll_number": "string",
                "student_full_name": "string",
                "outcome": "string",
                "detail": "string"
            }
        ]
    }
    ```

### Get Homeroom Class Attendance

*   **HTTP Method:** `GET`
*   **URL Path:** `/api/v1/teachers/homeroom-attendance/{class_code}/{attendance_date_str}/{session_str}`
*   **Brief Description:** Get all attendance records for a specific homeroom class, date, and session.
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

## Admin Student Attendance

### Get Student Attendance Records

*   **HTTP Method:** `GET`
*   **URL Path:** `/api/v1/admin/attendance/student/{student_roll_number}`
*   **Brief Description:** Admin: Get Student Attendance Records by Roll Number
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

### Get Classroom Attendance

*   **HTTP Method:** `GET`
*   **URL Path:** `/api/v1/admin/attendance/class/{class_code}/{attendance_date_str}/{session_str}`
*   **Brief Description:** Admin: Get Classroom Attendance by Date and Session
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

### Get Classroom Attendance Summary

*   **HTTP Method:** `GET`
*   **URL Path:** `/api/v1/admin/attendance/class/{class_code}/{attendance_date_str}/{session_str}/summary`
*   **Brief Description:** Admin: Get Classroom Attendance Percentage Summary
*   **Expected Response:**
    ```json
    {
        "school_class_id": "integer",
        "school_class_code": "string",
        "attendance_date": "date",
        "session": "string",
        "total_students_in_class": "integer",
        "present_count": "integer",
        "absent_count": "integer",
        "late_count": "integer",
        "excused_count": "integer",
        "unmarked_count": "integer",
        "present_percentage": "float",
        "absent_percentage": "float"
    }
    ```

### Delete Student Attendance Record

*   **HTTP Method:** `DELETE`
*   **URL Path:** `/api/v1/admin/attendance/{record_id}`
*   **Brief Description:** Admin: Delete a Student Attendance Record
*   **Expected Response:**
    ```json
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
    ```