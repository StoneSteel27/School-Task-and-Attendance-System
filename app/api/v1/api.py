from fastapi import APIRouter

from app.api.v1.endpoints import auth, users, classes, teachers, holidays, students

api_router_v1 = APIRouter()

api_router_v1.include_router(auth.router, prefix="/auth", tags=["Authentication"])

api_router_v1.include_router(users.router, prefix="/users", tags=["Users"])

api_router_v1.include_router(classes.router, prefix="/classes", tags=["School Classes"])

api_router_v1.include_router(teachers.router, prefix="/teachers", tags=["Teachers"])

api_router_v1.include_router(holidays.router, prefix="/holidays", tags=["Holidays"])

api_router_v1.include_router(students.router, prefix="/students", tags=["Students"])