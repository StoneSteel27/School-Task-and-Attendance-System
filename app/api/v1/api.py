# app/api/v1/api.py
from fastapi import APIRouter

from app.api.v1.endpoints.auth import auth_router, users_router, qr_login_router, recovery_router, users_admin_router
from app.api.v1.endpoints.core import classes_router, teachers_router, holidays_router, students_router, classes_admin_router, holidays_admin_router, students_teacher_router
from app.api.v1.endpoints.attendance import attendance_router, student_attendance_admin_router, homeroom_attendance_teacher_router
from app.api.v1.endpoints.academic import announcements_admin_router, submissions_teacher_router, tasks_announcements_teacher_router

api_router_v1 = APIRouter()

# Authentication endpoints
api_router_v1.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_router_v1.include_router(qr_login_router, prefix="/auth", tags=["Authentication"])
api_router_v1.include_router(recovery_router, prefix="/auth", tags=["Authentication"])
api_router_v1.include_router(users_router, prefix="/users", tags=["Users"])

# Core endpoints
api_router_v1.include_router(classes_router, prefix="/classes", tags=["School Classes"])
api_router_v1.include_router(teachers_router, prefix="/teachers", tags=["Teachers"])
api_router_v1.include_router(holidays_router, prefix="/holidays", tags=["Holidays"])
api_router_v1.include_router(students_router, prefix="/students", tags=["Students"])

# Teacher-specific endpoints
api_router_v1.include_router(students_teacher_router, prefix="/teachers", tags=["Teachers"])
api_router_v1.include_router(submissions_teacher_router, prefix="/teachers", tags=["Teachers"])
api_router_v1.include_router(tasks_announcements_teacher_router, prefix="/teachers", tags=["Teachers"])
api_router_v1.include_router(homeroom_attendance_teacher_router, prefix="/teachers/homeroom-attendance", tags=["Teachers"])

# Attendance endpoints
api_router_v1.include_router(attendance_router, prefix="/attendance", tags=["Attendance"])

# Admin endpoints
api_router_v1.include_router(users_admin_router, prefix="/admin/users", tags=["Administration"])
api_router_v1.include_router(classes_admin_router, prefix="/admin/classes", tags=["Administration"])
api_router_v1.include_router(holidays_admin_router, prefix="/admin/holidays", tags=["Administration"])
api_router_v1.include_router(student_attendance_admin_router, prefix="/admin/attendance", tags=["Administration"])
api_router_v1.include_router(announcements_admin_router, prefix="/admin/announcements", tags=["Administration"])
