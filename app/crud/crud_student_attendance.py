# app/crud/crud_student_attendance.py
from datetime import date
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from app import models

from app.models.student_attendance import StudentAttendance, AttendanceSession, AttendanceStatus
from app.models.user import User
from app.models.school_class import SchoolClass
from app.schemas.student_attendance import StudentAttendanceEntryInput  # For type hinting the entries


# We will return data that will be used to build ClassAttendanceSubmissionResultItem, not the schema itself from CRUD

def get_student_attendance_by_id(db: Session, attendance_id: int) -> Optional[StudentAttendance]:
    return (
        db.query(StudentAttendance)
        .options(
            joinedload(StudentAttendance.student),
            joinedload(StudentAttendance.school_class),
            joinedload(StudentAttendance.marked_by_teacher)
        )
        .filter(StudentAttendance.id == attendance_id)
        .first()
    )


def get_student_attendance_for_student_date_session(
        db: Session, student_id: int, attendance_date: date, session: AttendanceSession
) -> Optional[StudentAttendance]:
    return (
        db.query(StudentAttendance)
        .filter(
            StudentAttendance.student_id == student_id,
            StudentAttendance.attendance_date == attendance_date,
            StudentAttendance.session == session
        )
        .first()
    )


def get_attendance_for_class_on_date_session(
        db: Session, school_class_id: int, attendance_date: date, session: AttendanceSession
) -> List[StudentAttendance]:
    return (
        db.query(StudentAttendance)
        .options(
            joinedload(StudentAttendance.student),
            # joinedload(StudentAttendance.school_class), # Already filtered by school_class_id
            joinedload(StudentAttendance.marked_by_teacher)
        )
        .filter(
            StudentAttendance.school_class_id == school_class_id,
            StudentAttendance.attendance_date == attendance_date,
            StudentAttendance.session == session
        )
        .order_by(StudentAttendance.student_id)  # Or student.roll_number if joining User
        .all()
    )


def get_attendance_for_student_date_range(
        db: Session, student_id: int, start_date: date, end_date: date, skip: int = 0, limit: int = 100
) -> List[StudentAttendance]:
    return (
        db.query(StudentAttendance)
        .options(
            # joinedload(StudentAttendance.student), # Already filtered by student_id
            joinedload(StudentAttendance.school_class),
            joinedload(StudentAttendance.marked_by_teacher)
        )
        .filter(
            StudentAttendance.student_id == student_id,
            StudentAttendance.attendance_date >= start_date,
            StudentAttendance.attendance_date <= end_date
        )
        .order_by(StudentAttendance.attendance_date.desc(), StudentAttendance.session.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


# This will be the main function for creating records based on teacher submission
def create_class_attendance_records(
        db: Session,
        *,
        entries: List[StudentAttendanceEntryInput],  # List of {student_id, status}
        attendance_date: date,
        session: AttendanceSession,
        school_class_id: int,
        teacher_id: int
) -> List[Dict[str, Any]]:  # Returns a list of dicts to build ClassAttendanceSubmissionResultItem

    results: List[Dict[str, Any]] = []
    records_to_create: List[StudentAttendance] = []

    # 1. Get the SchoolClass ORM object and its students' IDs
    target_class = db.query(SchoolClass).options(joinedload(SchoolClass.students)).filter(
        SchoolClass.id == school_class_id).first()
    if not target_class:
        # This should ideally be caught by the endpoint before calling CRUD
        # If it happens, all entries will fail with a generic class error
        for entry in entries:
            results.append({
                "student_id": entry.student_id,
                "submitted_status": entry.status,
                "outcome": "ERROR_CLASS_NOT_FOUND_IN_CRUD",  # Specific error
                "message": f"Target class ID {school_class_id} not found during CRUD operation.",
                "record_id": None
            })
        return results

    students_in_class_ids = {student.id for student in target_class.students}

    # 2. Fetch all student User objects mentioned in entries for quick lookup
    # This helps avoid N+1 queries for student roll_number/name later if needed for response
    submitted_student_ids = {entry.student_id for entry in entries}
    students_in_payload = db.query(User).filter(User.id.in_(submitted_student_ids)).all()
    students_map = {student.id: student for student in students_in_payload}

    for entry in entries:
        student_id = entry.student_id
        submitted_status = entry.status

        student_orm = students_map.get(student_id)

        # Default result for this entry
        current_result = {
            "student_id": student_id,
            "student_roll_number": student_orm.roll_number if student_orm else "N/A",
            "student_full_name": student_orm.full_name if student_orm else "N/A",
            "submitted_status": submitted_status,
            "outcome": "ERROR_UNKNOWN",  # Default, should be overwritten
            "message": None,
            "record_id": None
        }

        if not student_orm:
            current_result["outcome"] = "ERROR_STUDENT_NOT_FOUND_IN_SYSTEM"
            current_result["message"] = f"Student ID {student_id} not found in the system."
            results.append(current_result)
            continue

        if student_orm.role != "student":
            current_result["outcome"] = "ERROR_USER_NOT_A_STUDENT"
            current_result["message"] = f"User ID {student_id} (Roll: {student_orm.roll_number}) is not a student."
            results.append(current_result)
            continue

        # Check if student belongs to the target class for this attendance
        # This check uses the student's current enrollment (student.school_class_id)
        # The `students_in_class_ids` set is based on the `target_class.students` relationship, which is also current.
        if student_id not in students_in_class_ids or student_orm.school_class_id != school_class_id:
            current_result["outcome"] = "ERROR_STUDENT_NOT_IN_SPECIFIED_CLASS"
            current_result[
                "message"] = f"Student ID {student_id} (Roll: {student_orm.roll_number}) is not enrolled in class ID {school_class_id}."
            results.append(current_result)
            continue

        # Check for existing record
        existing_record = get_student_attendance_for_student_date_session(
            db, student_id=student_id, attendance_date=attendance_date, session=session
        )
        if existing_record:
            current_result["outcome"] = "ERROR_ALREADY_RECORDED"
            current_result["message"] = (
                f"Attendance for student ID {student_id} (Roll: {student_orm.roll_number}) on {attendance_date} for {session.value} "
                f"session already exists with status {existing_record.status.value} (ID: {existing_record.id})."
            )
            current_result["record_id"] = existing_record.id  # Include existing record ID
            results.append(current_result)
            continue

        # If all checks pass, prepare to create the record
        new_attendance_record = StudentAttendance(
            student_id=student_id,
            school_class_id=school_class_id,  # From parameter
            marked_by_teacher_id=teacher_id,  # From parameter
            attendance_date=attendance_date,  # From parameter
            session=session,  # From parameter
            status=submitted_status  # From entry
        )
        records_to_create.append(new_attendance_record)
        # Temporarily mark as success, will update record_id after commit
        current_result["outcome"] = "SUCCESS_PENDING_COMMIT"
        current_result["message"] = "Record queued for creation."
        results.append(current_result)

    if records_to_create:
        try:
            db.add_all(records_to_create)
            db.commit()
            for i, record_orm in enumerate(records_to_create):
                db.refresh(record_orm)
                # Find corresponding result entry and update it
                for res_item in results:
                    # Match by student_id and the pending success status
                    if res_item["student_id"] == record_orm.student_id and res_item[
                        "outcome"] == "SUCCESS_PENDING_COMMIT":
                        res_item["outcome"] = "SUCCESS"
                        res_item["message"] = "Attendance record created successfully."
                        res_item["record_id"] = record_orm.id
                        break
        except IntegrityError as e:
            db.rollback()
            # This is a fallback, ideally individual checks prevent this.
            # Could be a race condition or unhandled unique constraint.
            # Mark all pending records as failed due to commit error.
            for res_item in results:
                if res_item["outcome"] == "SUCCESS_PENDING_COMMIT":
                    res_item["outcome"] = "ERROR_COMMIT_FAILED"
                    res_item["message"] = f"Database commit failed: {str(e)}"
        except Exception as e:
            db.rollback()
            for res_item in results:
                if res_item["outcome"] == "SUCCESS_PENDING_COMMIT":
                    res_item["outcome"] = "ERROR_UNKNOWN_COMMIT"
                    res_item["message"] = f"An unexpected error occurred during commit: {str(e)}"

    return results


def get_class_attendance_summary(
        db: Session, *, school_class_id: int, attendance_date: date, session: AttendanceSession
) -> Optional[Dict[str, Any]]:
    """
    Calculates and returns a summary of attendance for a given class, date, and session.
    The returned dictionary is structured to match the ClassAttendancePercentageSummary schema.
    Returns None if the school class is not found.
    """
    db_class = (
        db.query(models.SchoolClass)  # Assuming models is imported where SchoolClass is defined
        .options(joinedload(models.SchoolClass.students))
        .filter(models.SchoolClass.id == school_class_id)
        .first()
    )

    if not db_class:
        return None  # Class not found, API layer should handle 404

    total_students_enrolled = len(db_class.students)

    # Fetch all attendance records for this class, date, and session
    # This reuses an existing CRUD function.
    attendance_records_orm: List[models.StudentAttendance] = get_attendance_for_class_on_date_session(
        db=db, school_class_id=school_class_id, attendance_date=attendance_date, session=session
    )

    total_present = 0
    total_absent = 0
    for record in attendance_records_orm:
        # We only count records for students who are currently enrolled in this class.
        # This is an important check if attendance records are not hard-deleted when a student unenrolls
        # or if a student was marked for a class they are no longer in.
        # However, `get_attendance_for_class_on_date_session` already filters by school_class_id,
        # implicitly meaning these records are for students considered part of that class *at the time of marking*.
        # For calculating percentages against *current* enrollment, `total_students_enrolled` from `db_class.students` is key.
        # The current `attendance_records_orm` list only contains records for the specified class_id.
        if record.status == models.AttendanceStatus.PRESENT:
            total_present += 1
        elif record.status == models.AttendanceStatus.ABSENT:
            total_absent += 1
        # Not counting other statuses if any were to be added later

    total_marked = total_present + total_absent
    # total_unmarked represents currently enrolled students for whom no record was found for this session
    total_unmarked = total_students_enrolled - total_marked
    # Ensure total_unmarked is not negative, which could happen if records exist for students no longer enrolled.
    # However, our current logic focuses on current enrollment vs. marks for current class.
    # If total_marked > total_students_enrolled, it implies an data inconsistency (more marks than students).
    # For now, let's assume total_marked <= total_students_enrolled.
    if total_unmarked < 0:
        total_unmarked = 0  # Or log a data integrity issue.

    # Calculate percentages, handling division by zero
    attendance_percentage = (total_present / total_marked) * 100.0 if total_marked > 0 else 0.0
    marking_completeness_percentage = (
                                                  total_marked / total_students_enrolled) * 100.0 if total_students_enrolled > 0 else 0.0

    return {
        "school_class_id": db_class.id,
        "school_class_code": db_class.class_code,
        "school_class_name": db_class.name,
        "attendance_date": attendance_date,
        "session": session,  # This will be the AttendanceSession enum member
        "total_students_enrolled": total_students_enrolled,
        "total_marked": total_marked,
        "total_present": total_present,
        "total_absent": total_absent,
        "total_unmarked": total_unmarked,
        "attendance_percentage": round(attendance_percentage, 2),  # Round to 2 decimal places
        "marking_completeness_percentage": round(marking_completeness_percentage, 2),  # Round
    }
