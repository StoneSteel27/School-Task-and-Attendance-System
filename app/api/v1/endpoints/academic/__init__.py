# Academic content endpoints
from .announcements_admin import router as announcements_admin_router
from .submissions_teacher import router as submissions_teacher_router
from .tasks_announcements_teacher import router as tasks_announcements_teacher_router

__all__ = ["announcements_admin_router", "submissions_teacher_router", "tasks_announcements_teacher_router"]