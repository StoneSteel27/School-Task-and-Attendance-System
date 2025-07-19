import pytest # Add this if not already present for other test files
import datetime
import uuid # For generating unique identifiers

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session as SQLAlchemySession # Using the alias from conftest

from app.core.config import settings
# Import schemas needed for payload and response validation if desired, though direct dicts are often used for payloads
# from app.schemas.auth.user import UserCreate, UserUpdate
# from app.schemas.core.school_class import SchoolClassCreate, SchoolClassUpdate
# from app.schemas.attendance.student_attendance import ClassAttendanceSubmission, StudentAttendanceEntryInput
from app.models.attendance.student_attendance import AttendanceSession, AttendanceStatus # For enum values
from app.models.auth.user import User as UserModel # For type hinting if needed

# Helper functions for random data (can be moved to a common test utility later)
def random_email() -> str:
    return f"workflow-{uuid.uuid4().hex[:10]}@example.com"

def random_roll_number(prefix: str = "WF-RN") -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8].upper()}"

def random_password() -> str:
    return f"wf-pwd-{uuid.uuid4().hex[:8]}"

# Main test function for the workflow
def test_full_attendance_workflow(
    client: TestClient,
    superuser_token_headers: dict[str, str], # Fixture from conftest.py
    db: SQLAlchemySession # Fixture from conftest.py, aliased to avoid conflict
):
    admin_headers = superuser_token_headers

    # --- 1. Admin Setup Phase ---
    # Create School Class
    class_code = random_roll_number("WF-CLS")
    class_name = f"Workflow Class {class_code}"
    class_payload = {
        "class_code": class_code,
        "name": class_name,
        "grade": "10",
        "section": "A",
        "description": "Class for workflow testing"
    }
    response = client.post(
        f"{settings.API_V1_STR}/admin/classes/",
        headers=admin_headers,
        json=class_payload
    )
    assert response.status_code == 201, f"Failed to create class: {response.json()}"
    created_class_data = response.json()
    assert created_class_data["class_code"] == class_code
    school_class_id = created_class_data["id"]

    # Create Homeroom Teacher
    teacher_email = random_email()
    teacher_roll = random_roll_number("WF-TCH")
    teacher_pwd = random_password()
    teacher_full_name = f"Teacher {teacher_roll}"
    teacher_payload = {
        "email": teacher_email,
        "password": teacher_pwd,
        "roll_number": teacher_roll,
        "full_name": teacher_full_name,
        "role": "teacher",
        "is_active": True,
        "is_superuser": False,
    }
    response = client.post(
        f"{settings.API_V1_STR}/admin/users/",
        headers=admin_headers,
        json=teacher_payload
    )
    assert response.status_code == 201, f"Failed to create teacher: {response.json()}"
    created_teacher_data = response.json()
    teacher_id = created_teacher_data["id"]

    # Create Students
    student1_email = random_email()
    student1_roll = random_roll_number("WF-STU1")
    student1_pwd = random_password() # Password for student user
    student1_full_name = f"Student {student1_roll}"
    student1_payload = {
        "email": student1_email, "password": student1_pwd, "roll_number": student1_roll,
        "full_name": student1_full_name, "role": "student", "is_active": True
    }
    response = client.post(f"{settings.API_V1_STR}/admin/users/", headers=admin_headers, json=student1_payload)
    assert response.status_code == 201, f"Failed to create student 1: {response.json()}"
    created_student1_data = response.json()
    student1_id = created_student1_data["id"]

    student2_email = random_email()
    student2_roll = random_roll_number("WF-STU2")
    student2_pwd = random_password() # Password for student user
    student2_full_name = f"Student {student2_roll}"
    student2_payload = {
        "email": student2_email, "password": student2_pwd, "roll_number": student2_roll,
        "full_name": student2_full_name, "role": "student", "is_active": True
    }
    response = client.post(f"{settings.API_V1_STR}/admin/users/", headers=admin_headers, json=student2_payload)
    assert response.status_code == 201, f"Failed to create student 2: {response.json()}"
    created_student2_data = response.json()
    student2_id = created_student2_data["id"]

    # Assign Homeroom Teacher to Class
    # This relies on SchoolClassUpdate schema and CRUD handling homeroom_teacher_id
    # (as noted in previous thought process, this requires a schema change)
    update_class_payload_for_homeroom = {"homeroom_teacher_id": teacher_id}
    response = client.put(
        f"{settings.API_V1_STR}/admin/classes/{class_code}",
        headers=admin_headers,
        json=update_class_payload_for_homeroom
    )
    assert response.status_code == 200, f"Failed to assign homeroom teacher: {response.json()}"
    # The assertion below also depends on SchoolClass response schema including homeroom_teacher_id
    # assert response.json()["homeroom_teacher_id"] == teacher_id

    # Assign Students to Class
    assign_students_payload = {"student_roll_numbers": [student1_roll, student2_roll]}
    response = client.post(
        f"{settings.API_V1_STR}/admin/classes/{class_code}/students/class-assign",
        headers=admin_headers,
        json=assign_students_payload
    )
    assert response.status_code == 207, f"Failed to assign students: {response.json()}"
    assignment_results = response.json()
    for res in assignment_results:
        assert res["status"] == "assigned", f"Student {res['student_roll_number']} not assigned: {res['detail']}"


    # --- 2. Teacher Action: Login and Submit Attendance ---
    # Get Teacher's Token
    teacher_login_data = {"username": teacher_email, "password": teacher_pwd}
    response = client.post(f"{settings.API_V1_STR}/auth/login/access-token", data=teacher_login_data)
    assert response.status_code == 200, f"Teacher login failed: {response.json()}"
    teacher_token = response.json()["access_token"]
    teacher_auth_headers = {"Authorization": f"Bearer {teacher_token}"}

    # Prepare and Submit Attendance
    attendance_date = datetime.date.today().isoformat()
    attendance_session = AttendanceSession.MORNING.value # Use enum value

    submit_attendance_payload = {
        "attendance_date": attendance_date,
        "session": attendance_session,
        "entries": [
            {"student_id": student1_id, "status": AttendanceStatus.PRESENT.value},
            {"student_id": student2_id, "status": AttendanceStatus.ABSENT.value}
        ]
    }
    response = client.post(
        f"{settings.API_V1_STR}/teachers/homeroom-attendance/{class_code}/submit",
        headers=teacher_auth_headers,
        json=submit_attendance_payload
    )
    assert response.status_code == 201, f"Attendance submission failed: {response.json()}"
    submission_response_data = response.json()
    assert submission_response_data["school_class_code"] == class_code
    assert submission_response_data["successful_records"] == 2
    assert submission_response_data["failed_records"] == 0
    for result_item in submission_response_data["results"]:
        assert result_item["outcome"] == "SUCCESS"
        assert result_item["record_id"] is not None


    # --- 3. Teacher Verification: Get Attendance Records ---
    response = client.get(
        f"{settings.API_V1_STR}/teachers/homeroom-attendance/{class_code}/{attendance_date}/{attendance_session}",
        headers=teacher_auth_headers
    )
    assert response.status_code == 200, f"Teacher get attendance failed: {response.json()}"
    teacher_fetched_records = response.json()
    assert len(teacher_fetched_records) == 2

    # Verify Student 1
    s1_record_teacher_view = next((r for r in teacher_fetched_records if r["student"]["id"] == student1_id), None)
    assert s1_record_teacher_view is not None
    assert s1_record_teacher_view["status"] == AttendanceStatus.PRESENT.value
    assert s1_record_teacher_view["marked_by_teacher"]["id"] == teacher_id
    assert s1_record_teacher_view["school_class"]["id"] == school_class_id

    # Verify Student 2
    s2_record_teacher_view = next((r for r in teacher_fetched_records if r["student"]["id"] == student2_id), None)
    assert s2_record_teacher_view is not None
    assert s2_record_teacher_view["status"] == AttendanceStatus.ABSENT.value
    assert s2_record_teacher_view["marked_by_teacher"]["id"] == teacher_id
    assert s2_record_teacher_view["school_class"]["id"] == school_class_id


    # --- 4. Admin Verification: Get Attendance Records ---
    response = client.get(
        f"{settings.API_V1_STR}/admin/attendance/class/{class_code}/{attendance_date}/{attendance_session}",
        headers=admin_headers
    )
    assert response.status_code == 200, f"Admin get attendance failed: {response.json()}"
    admin_fetched_records = response.json()
    assert len(admin_fetched_records) == 2

    # Verify Student 1
    s1_record_admin_view = next((r for r in admin_fetched_records if r["student"]["id"] == student1_id), None)
    assert s1_record_admin_view is not None
    assert s1_record_admin_view["status"] == AttendanceStatus.PRESENT.value
    assert s1_record_admin_view["marked_by_teacher"]["id"] == teacher_id
    assert s1_record_admin_view["school_class"]["id"] == school_class_id

    # Verify Student 2
    s2_record_admin_view = next((r for r in admin_fetched_records if r["student"]["id"] == student2_id), None)
    assert s2_record_admin_view is not None
    assert s2_record_admin_view["status"] == AttendanceStatus.ABSENT.value
    assert s2_record_admin_view["marked_by_teacher"]["id"] == teacher_id
    assert s2_record_admin_view["school_class"]["id"] == school_class_id


    # --- 5. Admin Verification: Get Attendance Summary ---
    response = client.get(
        f"{settings.API_V1_STR}/admin/attendance/class/{class_code}/{attendance_date}/{attendance_session}/summary",
        headers=admin_headers
    )
    assert response.status_code == 200, f"Admin get attendance summary failed: {response.json()}"
    summary_data = response.json()

    assert summary_data["school_class_id"] == school_class_id
    assert summary_data["school_class_code"] == class_code
    assert summary_data["attendance_date"] == attendance_date
    assert summary_data["session"] == attendance_session
    assert summary_data["total_students_enrolled"] == 2
    assert summary_data["total_marked"] == 2
    assert summary_data["total_present"] == 1
    assert summary_data["total_absent"] == 1
    assert summary_data["total_unmarked"] == 0
    assert summary_data["attendance_percentage"] == 50.0
    assert summary_data["marking_completeness_percentage"] == 100.0

    # --- Cleanup (Optional, as DB transaction rollback in fixture should handle it) ---
    # If not relying on transaction rollback, you'd delete created items here in reverse order.
    # e.g., client.delete(f"/admin/users/{student1_roll}", headers=admin_headers)
    # client.delete(f"/admin/users/{student2_roll}", headers=admin_headers)
    # client.delete(f"/admin/users/{teacher_roll}", headers=admin_headers)
    # client.delete(f"/admin/classes/{class_code}", headers=admin_headers)