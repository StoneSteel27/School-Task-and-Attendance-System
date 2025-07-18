# app/api/v1/endpoints/teacher/__init__.py
from fastapi import APIRouter
from .homeroom_attendance import router as homeroom_attendance_router
from .tasks_announcements import router as tasks_announcements_router
from .students import router as students_router

teacher_router = APIRouter()

teacher_router.include_router(
    homeroom_attendance_router,
    prefix="/homeroom-attendance", # This prefix applies to all routes in homeroom_attendance.py
    tags=["Teacher - Homeroom Attendance"]
)

teacher_router.include_router(
    tasks_announcements_router,
    prefix="", # No additional prefix, routes will be /teacher/classes/{class_code}/tasks etc.
    tags=["Teacher - Tasks & Announcements"]
)

teacher_router.include_router(
    students_router,
    prefix="/students",
    tags=["Teacher - Students"]
)

# If you add more teacher-specific modules (e.g., teacher_tasks.py), include their routers here.
