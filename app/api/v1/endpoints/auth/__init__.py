# Authentication and security related endpoints
from .auth import router as auth_router
from .qr_login import router as qr_login_router
from .recovery import router as recovery_router
from .users import router as users_router
from .users_admin import router as users_admin_router

__all__ = ["auth_router", "qr_login_router", "recovery_router", "users_router", "users_admin_router"]