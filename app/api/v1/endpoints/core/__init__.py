# Core school structure endpoints
from .classes import router as classes_router
from .holidays import router as holidays_router
from .students import router as students_router
from .teachers import router as teachers_router
from .classes_admin import router as classes_admin_router
from .holidays_admin import router as holidays_admin_router
from .students_teacher import router as students_teacher_router

__all__ = ["classes_router", "holidays_router", "students_router", "teachers_router", 
           "classes_admin_router", "holidays_admin_router", "students_teacher_router"]