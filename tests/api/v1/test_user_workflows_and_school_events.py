# tests/api/v1/test_user_workflows_and_school_events.py

import pytest
import datetime
import uuid
from typing import List, Dict, Any, Optional

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session as SQLAlchemySession

from app.core.config import settings
from app.models.student_attendance import AttendanceSession, AttendanceStatus
from app.models.user import User as UserModel # For type hints

# --- Helper Functions for Test Setup ---

def _random_email() -> str:
    return f"workflow-user-{uuid.uuid4().hex[:10]}@example.com"

def _random_roll_number(prefix: str = "WF-RN") -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8].upper()}"

def _random_password() -> str:
    return f"wf-pwd-{uuid.uuid4().hex[:8]}"

def _get_auth_headers_for_user(client: TestClient, email: str, password: str) -> Dict[str, str]:
    login_data = {"username": email, "password": password}
    response = client.post(f"{settings.API_V1_STR}/auth/login/access-token", data=login_data)
    assert response.status_code == 200, f"Login failed for {email}: {response.json()}"
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def _create_user_util(
    client: TestClient,
    admin_headers: Dict[str, str],
    email: str,
    roll_number: str,
    password: str,
    full_name: str,
    role: str,
    is_active: bool = True,
    is_superuser: bool = False,
) -> Dict[str, Any]:
    payload = {
        "email": email,
        "password": password,
        "roll_number": roll_number,
        "full_name": full_name,
        "role": role,
        "is_active": is_active,
        "is_superuser": is_superuser,
    }
    response = client.post(f"{settings.API_V1_STR}/admin/users/", headers=admin_headers, json=payload)
    assert response.status_code == 201, f"Failed to create user {email} ({roll_number}): {response.json()}"
    return response.json()

def _create_class_util(
    client: TestClient,
    admin_headers: Dict[str, str],
    class_code: str,
    name: str,
    grade: str,
    section: str,
    description: Optional[str] = "Test class for workflows",
) -> Dict[str, Any]:
    payload = {
        "class_code": class_code,
        "name": name,
        "grade": grade,
        "section": section,
        "description": description,
    }
    response = client.post(f"{settings.API_V1_STR}/admin/classes/", headers=admin_headers, json=payload)
    assert response.status_code == 201, f"Failed to create class {class_code}: {response.json()}"
    return response.json()

def _assign_homeroom_teacher_util(
    client: TestClient,
    admin_headers: Dict[str, str],
    class_code: str,
    teacher_id: int,
):
    payload = {"homeroom_teacher_id": teacher_id}
    response = client.put(
        f"{settings.API_V1_STR}/admin/classes/{class_code}",
        headers=admin_headers,
        json=payload,
    )
    assert response.status_code == 200, f"Failed to assign homeroom teacher to {class_code}: {response.json()}"
    assert response.json()["homeroom_teacher_id"] == teacher_id

def _assign_students_to_class_util(
    client: TestClient,
    admin_headers: Dict[str, str],
    class_code: str,
    student_roll_numbers: List[str],
):
    payload = {"student_roll_numbers": student_roll_numbers}
    response = client.post(
        f"{settings.API_V1_STR}/admin/classes/{class_code}/students/class-assign",
        headers=admin_headers,
        json=payload,
    )
    assert response.status_code == 207, f"Failed to assign students to {class_code}: {response.json()}"
    for res_item in response.json():
        assert res_item["status"] == "assigned", \
            f"Student {res_item['student_roll_number']} not assigned to {class_code}: {res_item['detail']}"

def _set_class_schedule_util(
    client: TestClient,
    admin_headers: Dict[str, str],
    class_code: str,
    slots_payload: List[Dict[str, Any]],
):
    payload = {"slots": slots_payload}
    response = client.post(
        f"{settings.API_V1_STR}/admin/classes/{class_code}/schedule",
        headers=admin_headers,
        json=payload,
    )
    assert response.status_code == 201, f"Failed to set schedule for {class_code}: {response.json()}"
    # Further assertions can be made on the response if needed

def _mark_attendance_util(
    client: TestClient,
    teacher_headers: Dict[str, str],
    class_code: str,
    attendance_date_iso: str,
    session: AttendanceSession,
    entries: List[Dict[str, Any]], # e.g., [{"student_id": 1, "status": "PRESENT"}]
):
    payload = {
        "attendance_date": attendance_date_iso,
        "session": session.value,
        "entries": entries,
    }
    response = client.post(
        f"{settings.API_V1_STR}/teacher/homeroom-attendance/{class_code}/submit",
        headers=teacher_headers,
        json=payload,
    )
    assert response.status_code == 201, f"Failed to mark attendance for {class_code}: {response.json()}"
    submission_response = response.json()
    assert submission_response["failed_records"] == 0, \
        f"Some attendance records failed for {class_code}: {submission_response['results']}"
    for result_item in submission_response["results"]:
        assert result_item["outcome"] == "SUCCESS"
        assert result_item["record_id"] is not None

def _create_task_util(
    client: TestClient,
    teacher_headers: Dict[str, str],
    class_code: str,
    title: str,
    description: str,
    due_date: datetime.date,
    subject: str,
    attachment_url: Optional[str] = None
) -> Dict[str, Any]:
    payload = {
        "title": title,
        "description": description,
        "due_date": due_date.isoformat(),
        "subject": subject,
        "attachment_url": attachment_url
    }
    response = client.post(
        f"{settings.API_V1_STR}/teacher/classes/{class_code}/tasks",
        json=payload,
        headers=teacher_headers
    )
    assert response.status_code == 201, f"Failed to create task {title} for {class_code}: {response.json()}"
    return response.json()

def _create_announcement_util(
    client: TestClient,
    user_headers: Dict[str, str], # Can be teacher or admin
    title: str,
    content: str,
    is_school_wide: bool,
    school_class_id: Optional[int] = None,
    subject: Optional[str] = None,
    attachment_url: Optional[str] = None,
    is_teacher_call: bool = False # NEW: Flag to indicate if the call is from a teacher
) -> Dict[str, Any]:
    payload = {
        "title": title,
        "content": content,
        "is_school_wide": is_school_wide,
        "school_class_id": school_class_id,
        "subject": subject,
        "attachment_url": attachment_url
    }
    # Teachers use /teacher/announcements, Admins use /admin/announcements
    if is_teacher_call:
        endpoint = f"{settings.API_V1_STR}/teacher/announcements"
    else:
        endpoint = f"{settings.API_V1_STR}/admin/announcements"

    response = client.post(
        endpoint,
        json=payload,
        headers=user_headers
    )
    assert response.status_code == 201, f"Failed to create announcement {title}: {response.json()}"
    return response.json()



# --- Test Scenarios ---

# Scenario 1: Student views their schedule and attendance
def test_student_views_schedule_and_attendance(
    client: TestClient,
    superuser_token_headers: dict[str, str], # For admin actions
    db: SQLAlchemySession # db fixture from conftest
):
    admin_headers = superuser_token_headers

    # 1. SETUP PHASE
    # Create School Class
    class_code = _random_roll_number("CLS-STU")
    class_name = f"Student Workflow Class {class_code}"
    created_class = _create_class_util(client, admin_headers, class_code, class_name, "5", "B")
    school_class_id = created_class["id"]

    # Create Homeroom Teacher
    teacher_email = _random_email()
    teacher_roll = _random_roll_number("TCH-STU")
    teacher_pwd = _random_password()
    teacher_full_name = f"Teacher {teacher_roll}"
    created_teacher = _create_user_util(
        client, admin_headers, teacher_email, teacher_roll, teacher_pwd, teacher_full_name, "teacher"
    )
    teacher_id = created_teacher["id"]
    _assign_homeroom_teacher_util(client, admin_headers, class_code, teacher_id)

    # Create Student S1
    s1_email = _random_email()
    s1_roll = _random_roll_number("STU1")
    s1_pwd = _random_password()
    s1_full_name = f"Student {s1_roll}"
    created_s1 = _create_user_util(client, admin_headers, s1_email, s1_roll, s1_pwd, s1_full_name, "student")
    s1_id = created_s1["id"]
    _assign_students_to_class_util(client, admin_headers, class_code, [s1_roll])

    # Define schedule for C1 (e.g., Math on Monday Period 1 by T1)
    # Monday is day_of_week=0
    today = datetime.date.today()
    monday_date = today - datetime.timedelta(days=today.weekday()) # Get current week's Monday
    # if today is Sat or Sun, this will be past Monday, adjust if future monday is needed for 'upcoming' logic
    # For simplicity, we'll use relative day_of_week for schedule template.

    schedule_slots_payload = [
        {
            "subject_name": "Mathematics",
            "day_of_week": 0, # Monday
            "period_number": 1,
            "teacher_id": teacher_id
        },
        {
            "subject_name": "Science",
            "day_of_week": 1, # Tuesday
            "period_number": 2,
            "teacher_id": teacher_id
        }
    ]
    _set_class_schedule_util(client, admin_headers, class_code, schedule_slots_payload)

    # Teacher T1 marks attendance for S1
    teacher_auth_headers = _get_auth_headers_for_user(client, teacher_email, teacher_pwd)
    attendance_date_iso = monday_date.isoformat()
    attendance_entries_s1_present = [{"student_id": s1_id, "status": AttendanceStatus.PRESENT.value}]
    _mark_attendance_util(
        client, teacher_auth_headers, class_code, attendance_date_iso,
        AttendanceSession.MORNING, attendance_entries_s1_present
    )

    # 2. STUDENT S1 ACTIONS
    s1_auth_headers = _get_auth_headers_for_user(client, s1_email, s1_pwd)

    # Test 2.1: S1 views weekly schedule
    response_weekly_schedule = client.get(
        f"{settings.API_V1_STR}/students/me/schedule",
        headers=s1_auth_headers
    )
    assert response_weekly_schedule.status_code == 200
    data_weekly = response_weekly_schedule.json()
    assert len(data_weekly) == 2 # Math on Mon, Science on Tue
    assert any(s["subject_name"] == "Mathematics" and s["day_of_week"] == 0 for s in data_weekly)
    assert any(s["subject_name"] == "Science" and s["day_of_week"] == 1 for s in data_weekly)

    # Test 2.2: S1 views schedule for specific day (Monday)
    response_daily_schedule = client.get(
        f"{settings.API_V1_STR}/students/me/schedule?target_date={monday_date.isoformat()}",
        headers=s1_auth_headers
    )
    assert response_daily_schedule.status_code == 200
    data_daily = response_daily_schedule.json()
    assert len(data_daily) == 1
    assert data_daily[0]["subject_name"] == "Mathematics"
    assert data_daily[0]["day_of_week"] == 0 # Monday

    # Test 2.3: S1 views schedule for a day with no classes (e.g., Wednesday if not scheduled)
    wednesday_date = monday_date + datetime.timedelta(days=2)
    response_empty_daily_schedule = client.get(
        f"{settings.API_V1_STR}/students/me/schedule?target_date={wednesday_date.isoformat()}",
        headers=s1_auth_headers
    )
    assert response_empty_daily_schedule.status_code == 200
    data_empty_daily = response_empty_daily_schedule.json()
    assert len(data_empty_daily) == 0

    # Test 2.4: S1 views attendance
    response_attendance = client.get(
        f"{settings.API_V1_STR}/students/me/attendance?startDate={monday_date.isoformat()}&endDate={monday_date.isoformat()}",
        headers=s1_auth_headers
    )
    assert response_attendance.status_code == 200
    data_attendance = response_attendance.json()
    assert len(data_attendance) == 1
    assert data_attendance[0]["status"] == AttendanceStatus.PRESENT.value
    assert data_attendance[0]["student"]["roll_number"] == s1_roll
    assert data_attendance[0]["attendance_date"] == monday_date.isoformat()
    assert data_attendance[0]["session"] == AttendanceSession.MORNING.value

    pass


def test_student_views_tasks_and_announcements(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: SQLAlchemySession
):
    admin_headers = superuser_token_headers

    # 1. SETUP PHASE
    # Create School Class
    class_code = _random_roll_number("CLS-TASK-ANN")
    class_name = f"Task/Ann Class {class_code}"
    created_class = _create_class_util(client, admin_headers, class_code, class_name, "6", "A")
    school_class_id = created_class["id"]

    # Create Teacher
    teacher_email = _random_email()
    teacher_roll = _random_roll_number("TCH-TASK-ANN")
    teacher_pwd = _random_password()
    teacher_full_name = f"Teacher {teacher_roll}"
    created_teacher = _create_user_util(
        client, admin_headers, teacher_email, teacher_roll, teacher_pwd, teacher_full_name, "teacher"
    )
    teacher_id = created_teacher["id"]
    teacher_auth_headers = _get_auth_headers_for_user(client, teacher_email, teacher_pwd)

    # Assign teacher to class and subject
    _ = client.post(
        f"{settings.API_V1_STR}/admin/classes/{class_code}/assign-teachers",
        headers=admin_headers,
        json={
            "assignments": [
                {"teacher_roll_number": teacher_roll, "subject": "History"},
                {"teacher_roll_number": teacher_roll, "subject": "Art"}
            ]
        }
    )

    # Create Student S1
    s1_email = _random_email()
    s1_roll = _random_roll_number("STU-TASK-ANN-1")
    s1_pwd = _random_password()
    s1_full_name = f"Student {s1_roll}"
    created_s1 = _create_user_util(client, admin_headers, s1_email, s1_roll, s1_pwd, s1_full_name, "student")
    s1_id = created_s1["id"]
    _assign_students_to_class_util(client, admin_headers, class_code, [s1_roll])
    s1_auth_headers = _get_auth_headers_for_user(client, s1_email, s1_pwd)

    # Create Student S2 (not assigned to any class)
    s2_email = _random_email()
    s2_roll = _random_roll_number("STU-TASK-ANN-2")
    s2_pwd = _random_password()
    s2_full_name = f"Student {s2_roll}"
    created_s2 = _create_user_util(client, admin_headers, s2_email, s2_roll, s2_pwd, s2_full_name, "student")
    s2_auth_headers = _get_auth_headers_for_user(client, s2_email, s2_pwd)

    # Create Tasks
    from datetime import date, timedelta
    task_history = _create_task_util(client, teacher_auth_headers, class_code, "History Essay", "Write about WWII", date.today() + timedelta(days=14), "History")
    task_art = _create_task_util(client, teacher_auth_headers, class_code, "Art Project", "Draw a landscape", date.today() + timedelta(days=21), "Art")

    # Create Announcements
    announcement_school_wide = _create_announcement_util(client, admin_headers, "School Fair", "Annual school fair next month.", True, is_teacher_call=False)
    announcement_class_specific = _create_announcement_util(client, teacher_auth_headers, "Class Trip", "Reminder about the field trip.", False, school_class_id=school_class_id, is_teacher_call=True)
    announcement_subject_specific = _create_announcement_util(client, teacher_auth_headers, "History Quiz", "Quiz on Chapter 5 next Friday.", False, school_class_id=school_class_id, subject="History", is_teacher_call=True)

    # 2. STUDENT S1 (ENROLLED) ACTIONS
    # Test 2.1: S1 views tasks
    response_s1_tasks = client.get(
        f"{settings.API_V1_STR}/students/me/tasks",
        headers=s1_auth_headers
    )
    assert response_s1_tasks.status_code == 200
    s1_tasks = response_s1_tasks.json()
    assert len(s1_tasks) == 2
    assert any(t["title"] == "History Essay" for t in s1_tasks)
    assert any(t["title"] == "Art Project" for t in s1_tasks)

    # Test 2.2: S1 views announcements
    response_s1_announcements = client.get(
        f"{settings.API_V1_STR}/students/me/announcements",
        headers=s1_auth_headers
    )
    assert response_s1_announcements.status_code == 200
    s1_announcements = response_s1_announcements.json()
    assert len(s1_announcements) == 3 # School-wide, Class-specific, Subject-specific
    assert any(a["title"] == "School Fair" and a["is_school_wide"] is True for a in s1_announcements)
    assert any(a["title"] == "Class Trip" and a["school_class_id"] == school_class_id for a in s1_announcements)
    assert any(a["title"] == "History Quiz" and a["school_class_id"] == school_class_id and a["subject"] == "History" for a in s1_announcements)

    # 3. STUDENT S2 (NOT ENROLLED) ACTIONS
    # Test 3.1: S2 tries to view tasks
    response_s2_tasks = client.get(
        f"{settings.API_V1_STR}/students/me/tasks",
        headers=s2_auth_headers
    )
    assert response_s2_tasks.status_code == 404 # Not enrolled in any class

    # Test 3.2: S2 tries to view announcements (should still see school-wide)
    response_s2_announcements = client.get(
        f"{settings.API_V1_STR}/students/me/announcements",
        headers=s2_auth_headers
    )
    assert response_s2_announcements.status_code == 200
    s2_announcements = response_s2_announcements.json()
    assert len(s2_announcements) == 1 # Only school-wide
    assert any(a["title"] == "School Fair" and a["is_school_wide"] is True for a in s2_announcements)
    assert not any(a["title"] == "Class Trip" for a in s2_announcements)

    pass