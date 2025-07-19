# Authentication and security related CRUD operations
from . import crud_user
from . import crud_recovery_code
from . import crud_qr_login_session
from . import crud_webauthn

# For backward compatibility, also export without prefix
from .crud_user import *
from .crud_recovery_code import *
from .crud_qr_login_session import *
from .crud_webauthn import *

# Export functions grouped by module name for easier access
user = crud_user
recovery_code = crud_recovery_code
qr_login_session = crud_qr_login_session
webauthn = crud_webauthn

__all__ = [
    "crud_user", "crud_recovery_code", "crud_qr_login_session", "crud_webauthn",
    "user", "recovery_code", "qr_login_session", "webauthn"
]
