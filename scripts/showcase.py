
import requests
import os
import random
from datetime import datetime, timedelta
import time
import logging
import sys

# --- Pre-run Setup: Add project root to path ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# --- Direct DB Imports for Initial Superuser ---
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.schemas.auth.user import UserCreate
from app.crud.auth import user as crud_user
from app.core.security import get_password_hash

# --- Configuration ---
BASE_URL = "http://127.0.0.1:8000/api/v1"
SUBMISSIONS_DIR = "submissions_showcase"

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Showcase Data ---
PRINCIPAL_DATA = {
    "email": "principal.main@school.com", "password": "strongpassword1", "full_name": "Dr. Evelyn Reed",
    "roll_number": "P001", "role": "principal", "is_superuser": True
}

# --- Helper Functions ---

def create_initial_superuser():
    """Creates the initial superuser directly in the database if they don't exist."""
    logging.info("Checking for initial superuser...")
    db: Session = SessionLocal()
    try:
        user = crud_user.get_user_by_email(db, email=PRINCIPAL_DATA["email"])
        if user:
            logging.info(f"Superuser '{PRINCIPAL_DATA['email']}' already exists.")
            if not user.is_superuser:
                user.is_superuser = True
                db.add(user)
                db.commit()
                logging.info("Promoted existing user to superuser.")
        else:
            logging.info(f"Creating superuser '{PRINCIPAL_DATA['email']}'...")
            password_hash = get_password_hash(PRINCIPAL_DATA["password"])
            # The password in UserCreate is for validation, not storage.
            # The actual hashed password is now passed separately.
            user_in = UserCreate(**PRINCIPAL_DATA)
            crud_user.create_user(db=db, user_in=user_in, password_hash=password_hash)
            logging.info("Successfully created superuser directly in the database.")
    finally:
        db.close()

def get_session():
    return requests.Session()

def login(session, email, password):
    logging.info(f"Attempting to log in as {email}...")
    try:
        response = session.post(f"{BASE_URL}/auth/login/access-token", data={"username": email, "password": password})
        response.raise_for_status()
        session.headers.update({"Authorization": f"Bearer {response.json()['access_token']}"})
        logging.info(f"Successfully logged in as {email}.")
        return True
    except requests.exceptions.HTTPError as e:
        logging.error(f"Login failed for {email}: {e.response.status_code} {e.response.text}")
        return False

def create_user_via_api(admin_session, user_data):
    roll_number = user_data['roll_number']
    logging.info(f"API: Creating user {user_data['full_name']} ({roll_number})...")
    try:
        response = admin_session.post(f"{BASE_URL}/admin/users/", json=user_data)
        if response.status_code == 400 and "already exists" in response.text:
            logging.warning(f"User {roll_number} already exists. Skipping.")
            return get_user(admin_session, roll_number)
        response.raise_for_status()
        logging.info(f"Successfully created user {roll_number} via API.")
        return response.json()
    except requests.exceptions.HTTPError as e:
        logging.error(f"Failed to create user {roll_number} via API: {e.response.status_code} {e.response.text}")
        return None

def get_user(admin_session, roll_number):
    try:
        response = admin_session.get(f"{BASE_URL}/admin/users/{roll_number}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError:
        return None

def create_class(admin_session, class_data):
    class_code = class_data['class_code']
    logging.info(f"Creating class {class_code}...")
    try:
        response = admin_session.post(f"{BASE_URL}/admin/classes/", json=class_data)
        if response.status_code == 400 and "already exists" in response.text:
            logging.warning(f"Class {class_code} already exists. Skipping.")
            return {"class_code": class_code, "id": get_class_id_by_code(admin_session, class_code)}
        response.raise_for_status()
        logging.info(f"Successfully created class {class_code}.")
        return response.json()
    except requests.exceptions.HTTPError as e:
        logging.error(f"Failed to create class {class_code}: {e.response.status_code} {e.response.text}")
        return None

def get_class_id_by_code(admin_session, class_code):
    try:
        response = admin_session.get(f"{BASE_URL}/classes/{class_code}")
        response.raise_for_status()
        return response.json().get("id")
    except requests.exceptions.HTTPError:
        return None

def assign_students_to_class(admin_session, class_code, student_roll_numbers):
    logging.info(f"Assigning {len(student_roll_numbers)} students to class {class_code}...")
    try:
        response = admin_session.post(f"{BASE_URL}/admin/classes/{class_code}/students/class-assign", json={"student_roll_numbers": student_roll_numbers})
        response.raise_for_status()
        time.sleep(0.1) # Add delay
    except requests.exceptions.HTTPError as e:
        logging.error(f"Failed to assign students to {class_code}: {e.response.status_code} {e.response.text}")

def assign_teachers_to_class(admin_session, class_code, assignments):
    logging.info(f"Assigning {len(assignments)} teacher roles in class {class_code}...")
    try:
        response = admin_session.post(f"{BASE_URL}/admin/classes/{class_code}/assign-teachers", json={"assignments": assignments})
        response.raise_for_status()
        time.sleep(0.1) # Add delay
    except requests.exceptions.HTTPError as e:
        logging.error(f"Failed to assign teachers to {class_code}: {e.response.status_code} {e.response.text}")

def create_school_announcement(admin_session, title, content):
    logging.info(f"Creating school-wide announcement: '{title}'")
    try:
        response = admin_session.post(f"{BASE_URL}/admin/announcements/", json={"title": title, "content": content, "is_school_wide": True})
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        logging.error(f"Failed to create school-wide announcement: {e.response.status_code} {e.response.text}")

def create_teacher_announcement(teacher_session, class_id, subject, title, content):
    logging.info(f"Teacher creating announcement '{title}' for subject {subject}...")
    try:
        payload = {"title": title, "content": content, "school_class_id": class_id, "subject": subject, "is_school_wide": False}
        response = teacher_session.post(f"{BASE_URL}/teachers/announcements", json=payload)
        response.raise_for_status()
        logging.info(f"Successfully created teacher announcement '{title}'.")
        return response.json()
    except requests.exceptions.HTTPError as e:
        logging.error(f"Failed to create teacher announcement: {e.response.status_code} {e.response.text}")
        return None

def create_teacher_task(teacher_session, class_code, subject, title, description, due_date):
    logging.info(f"Teacher creating task '{title}' for {class_code} in {subject}...")
    try:
        response = teacher_session.post(f"{BASE_URL}/teachers/classes/{class_code}/tasks", json={"title": title, "description": description, "subject": subject, "due_date": due_date.date().isoformat()})
        response.raise_for_status()
        logging.info(f"Successfully created task '{title}'.")
        return response.json()
    except requests.exceptions.HTTPError as e:
        logging.error(f"Failed to create task '{title}': {e.response.status_code} {e.response.text}")
        return None

def get_student_tasks(student_session):
    try:
        response = student_session.get(f"{BASE_URL}/students/me/tasks")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError:
        return []

def submit_task(student_session, task_id):
    logging.info(f"Student submitting task {task_id}...")
    dummy_filename = f"submission_task_{task_id}.txt"
    dummy_filepath = os.path.join(SUBMISSIONS_DIR, dummy_filename)
    os.makedirs(SUBMISSIONS_DIR, exist_ok=True)
    with open(dummy_filepath, "w") as f: f.write("Dummy submission.")
    try:
        with open(dummy_filepath, "rb") as f:
            response = student_session.post(f"{BASE_URL}/students/me/tasks/{task_id}/submit", files={"file": (dummy_filename, f, "text/plain")})
        response.raise_for_status()
        logging.info(f"Successfully submitted task {task_id}.")
        return response.json()
    except requests.exceptions.HTTPError as e:
        logging.error(f"Failed to submit task {task_id}: {e.response.status_code} {e.response.text}")
        return None
    finally:
        if os.path.exists(dummy_filepath): os.remove(dummy_filepath)

def get_task_submissions(teacher_session, task_id):
    logging.info(f"Teacher fetching submissions for task {task_id}...")
    try:
        response = teacher_session.get(f"{BASE_URL}/teachers/tasks/{task_id}/submissions")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError: return []

def approve_submission(teacher_session, submission_id):
    logging.info(f"Teacher approving submission {submission_id}...")
    try:
        response = teacher_session.put(f"{BASE_URL}/teachers/submissions/{submission_id}/approve")
        response.raise_for_status()
        logging.info(f"Successfully approved submission {submission_id}.")
        return response.json()
    except requests.exceptions.HTTPError as e:
        logging.error(f"Failed to approve submission: {e.response.status_code} {e.response.text}")

def submit_class_attendance(teacher_session, class_code, students):
    logging.info(f"Homeroom teacher for {class_code} submitting attendance...")
    entries = [{"student_id": s['id'], "status": random.choice(["PRESENT", "ABSENT"])} for s in students]
    payload = {"attendance_date": datetime.now().date().isoformat(), "session": "MORNING", "entries": entries}
    try:
        response = teacher_session.post(f"{BASE_URL}/teachers/homeroom-attendance/{class_code}/submit", json=payload)
        response.raise_for_status()
        logging.info(f"Successfully submitted attendance for {class_code}.")
    except requests.exceptions.HTTPError as e:
        logging.error(f"Failed to submit attendance for {class_code}: {e.response.status_code} {e.response.text}")

def showcase():
    logging.info("--- Starting Expanded School Backend Showcase ---")
    create_initial_superuser()
    admin_session = get_session()
    if not login(admin_session, PRINCIPAL_DATA["email"], PRINCIPAL_DATA["password"]):
        logging.error("Fatal: Could not log in as principal. Aborting.")
        return

    # Expanded Data
    teachers_data = [
        {"email": "teacher.math@school.com", "password": "password", "full_name": "Mr. Alan Turing", "roll_number": "T01", "role": "teacher"},
        {"email": "teacher.science@school.com", "password": "password", "full_name": "Ms. Marie Curie", "roll_number": "T02", "role": "teacher"},
        {"email": "teacher.history@school.com", "password": "password", "full_name": "Mr. Herod Otus", "roll_number": "T03", "role": "teacher"},
        {"email": "teacher.art@school.com", "password": "password", "full_name": "Mr. Leo Da Vinci", "roll_number": "T04", "role": "teacher"},
        {"email": "teacher.english@school.com", "password": "password", "full_name": "Ms. Jane Austen", "roll_number": "T05", "role": "teacher"},
        {"email": "teacher.pe@school.com", "password": "password", "full_name": "Mr. Jesse Owens", "roll_number": "T06", "role": "teacher"},
    ]
    students_data = [{"email": f"student{i}@school.com", "password": "password", "full_name": f"Student {i}", "roll_number": f"S{i:03}", "role": "student"} for i in range(1, 61)]

    created_users = []
    for user_data in teachers_data + students_data:
        user = create_user_via_api(admin_session, user_data)
        if user:
            created_users.append(user)
        time.sleep(0.1) # Add delay

    created_teachers = [u for u in created_users if u['role'] == 'teacher']
    created_students = [u for u in created_users if u['role'] == 'student']
    student_roll_numbers = [s['roll_number'] for s in created_students]

    # Get teacher IDs for class creation
    teacher_t01_id = next((t['id'] for t in created_teachers if t['roll_number'] == 'T01'), None)
    teacher_t02_id = next((t['id'] for t in created_teachers if t['roll_number'] == 'T02'), None)
    teacher_t05_id = next((t['id'] for t in created_teachers if t['roll_number'] == 'T05'), None)
    teacher_t06_id = next((t['id'] for t in created_teachers if t['roll_number'] == 'T06'), None)

    classes = [
        create_class(admin_session, {"name": "Class 9A", "class_code": "9A", "grade": "9", "homeroom_teacher_id": teacher_t01_id}),
        create_class(admin_session, {"name": "Class 9B", "class_code": "9B", "grade": "9", "homeroom_teacher_id": teacher_t02_id}),
        create_class(admin_session, {"name": "Class 10A", "class_code": "10A", "grade": "10", "homeroom_teacher_id": teacher_t05_id}),
        create_class(admin_session, {"name": "Class 10B", "class_code": "10B", "grade": "10", "homeroom_teacher_id": teacher_t06_id}),
    ]
    
    student_roll_numbers = [s['roll_number'] for s in students_data]
    assign_students_to_class(admin_session, "9A", student_roll_numbers[0:15])
    assign_students_to_class(admin_session, "9B", student_roll_numbers[15:30])
    assign_students_to_class(admin_session, "10A", student_roll_numbers[30:45])
    assign_students_to_class(admin_session, "10B", student_roll_numbers[45:60])

    assign_teachers_to_class(admin_session, "9A", [{"teacher_roll_number": "T01", "subject": "Mathematics"}, {"teacher_roll_number": "T02", "subject": "Science"}])
    assign_teachers_to_class(admin_session, "9B", [{"teacher_roll_number": "T01", "subject": "Mathematics"}, {"teacher_roll_number": "T03", "subject": "History"}])
    assign_teachers_to_class(admin_session, "10A", [{"teacher_roll_number": "T05", "subject": "English"}, {"teacher_roll_number": "T04", "subject": "Art"}])
    assign_teachers_to_class(admin_session, "10B", [{"teacher_roll_number": "T05", "subject": "English"}, {"teacher_roll_number": "T06", "subject": "Physical Education"}])

    create_school_announcement(admin_session, "Annual Sports Day", "The annual sports day will be held next month. Sign up now!")

    # Teacher Activities
    science_teacher_session = get_session()
    if login(science_teacher_session, "teacher.science@school.com", "password"):
        class_9a_id = next((c['id'] for c in classes if c['class_code'] == '9A'), None)
        if class_9a_id:
            create_teacher_announcement(science_teacher_session, class_9a_id, "Science", "Lab Safety", "Reminder: Lab coats are mandatory for the next practical class.")
            task1 = create_teacher_task(science_teacher_session, "9A", "Science", "Photosynthesis Report", "Write a 2-page report on photosynthesis.", datetime.now() + timedelta(days=10))
            task2 = create_teacher_task(science_teacher_session, "9A", "Science", "Volcano Model", "Build a model of a volcano. Due in 3 weeks.", datetime.now() + timedelta(days=21))

    # Student Submissions
    submitted_task_id = None
    if task1:
        submitted_task_id = task1.get('id')
        for i in range(1, 8): # First 7 students submit the first task
            student_session = get_session()
            if login(student_session, f"student{i}@school.com", "password"):
                submit_task(student_session, submitted_task_id)
                time.sleep(0.2)

    # Teacher Approves a Submission
    if submitted_task_id and login(science_teacher_session, "teacher.science@school.com", "password"):
        submissions = get_task_submissions(science_teacher_session, submitted_task_id)
        if submissions:
            submission_to_approve = next((s for s in submissions if s.get('status') == 'SUBMITTED'), None)
            if submission_to_approve:
                approve_submission(science_teacher_session, submission_to_approve['id'])
        else:
            logging.warning(f"No submissions found for task {submitted_task_id} to approve.")

    # Homeroom Teacher Submits Attendance
    math_teacher_session = get_session()
    if login(math_teacher_session, "teacher.math@school.com", "password"):
        # We need the student objects for their IDs
        students_in_9a = [s for s in created_students if s['roll_number'] in student_roll_numbers[0:15]]
        if students_in_9a:
            submit_class_attendance(math_teacher_session, "9A", students_in_9a)
        else:
            logging.warning("Could not find created student objects for class 9A to submit attendance.")

    logging.info("--- Expanded Showcase Finished ---")

if __name__ == "__main__":
    showcase()
