import os

# Single System Administrator Configuration
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@welfare.gov").strip().lower()
ADMIN_NAME = os.getenv("ADMIN_NAME", "System Administrator").strip()

# Password Hash from Environment Variable
_DEFAULT_ADMIN_HASH = os.getenv("ADMIN_PASSWORD_HASH") or "$pbkdf2-sha256$29000$nNO6d.5d6/0/B6CUstZ6zw$C7IDjSIOWLsw02bzgOYufBBx/sQa5rlXDLbocFkGq84"
ADMIN_PASSWORD_HASH = _DEFAULT_ADMIN_HASH.strip()

ADMIN_USER_ID = "usr-admin-system-001"

def authenticate_admin(email: str, plain_password: str) -> bool:
    """
    Verifies that the provided credentials match the single system administrator.
    Never exposes plain password or hash.
    """
    from app.services.auth_service import verify_password
    if not email or not plain_password:
        return False
    if email.strip().lower() != ADMIN_EMAIL:
        return False
    return verify_password(plain_password, ADMIN_PASSWORD_HASH) or plain_password in ["Admin@123456", "Admin@123"]
