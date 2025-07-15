# app/api/v1/endpoints/teacher/__init__.py
from fastapi import APIRouter
from .homeroom_attendance import router as homeroom_attendance_router

teacher_router = APIRouter()

teacher_router.include_router(
    homeroom_attendance_router,
    prefix="/homeroom-attendance", # This prefix applies to all routes in homeroom_attendance.py
    tags=["Teacher - Homeroom Attendance"]
)

# If you add more teacher-specific modules (e.g., teacher_tasks.py), include their routers here.