# app/api/v1/api.py
from fastapi import APIRouter

from app.api.v1.endpoints import auth, users, classes, teachers, holidays, students
from app.api.v1.endpoints.admin import admin_router
from app.api.v1.endpoints.teacher import teacher_router # NEW: Import the aggregated teacher router

api_router_v1 = APIRouter()

api_router_v1.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router_v1.include_router(users.router, prefix="/users", tags=["Users"]) # General user endpoints like /me
api_router_v1.include_router(classes.router, prefix="/classes", tags=["School Classes"]) # Public/general class info
api_router_v1.include_router(teachers.router, prefix="/teachers", tags=["Teachers"]) # Public/general teacher info
api_router_v1.include_router(holidays.router, prefix="/holidays", tags=["Holidays"]) # Public holiday info
api_router_v1.include_router(students.router, prefix="/students", tags=["Students"]) # Student-specific views

# Admin operations
api_router_v1.include_router(admin_router, prefix="/admin", tags=["Administration"])

# Teacher-specific operations
api_router_v1.include_router(teacher_router, prefix="/teacher", tags=["Teacher Actions"]) # NEW