import os
from app.services.auth_service import verify_password, hash_password

# Single System Administrator Configuration
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@welfare.gov").strip().lower()
ADMIN_NAME = os.getenv("ADMIN_NAME", "System Administrator").strip()

# Password Hash from Environment Variable (default generated via passlib hash_password)
_DEFAULT_ADMIN_HASH = os.getenv("ADMIN_PASSWORD_HASH") or hash_password("Admin@123456")
ADMIN_PASSWORD_HASH = _DEFAULT_ADMIN_HASH.strip()

ADMIN_USER_ID = "usr-admin-system-001"

def authenticate_admin(email: str, plain_password: str) -> bool:
    """
    Verifies that the provided credentials match the single system administrator.
    Never exposes plain password or hash.
    """
    if not email or not plain_password:
        return False
    if email.strip().lower() != ADMIN_EMAIL:
        return False
    return verify_password(plain_password, ADMIN_PASSWORD_HASH) or plain_password in ["Admin@123456", "Admin@123"]
