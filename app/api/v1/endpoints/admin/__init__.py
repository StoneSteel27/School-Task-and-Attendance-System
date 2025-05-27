from fastapi import APIRouter

from .users_admin import router as users_admin_router
from .classes_admin import router as classes_admin_router
from .holidays_admin import router as holidays_admin_router # NEW

admin_router = APIRouter()

admin_router.include_router(users_admin_router, prefix="/users", tags=["Admin - Users"])
admin_router.include_router(classes_admin_router, prefix="/classes", tags=["Admin - Classes"])
admin_router.include_router(holidays_admin_router, prefix="/holidays", tags=["Admin - Holidays"]) # NEW
