from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.database.supabase_db import db
from app.config import config

security_scheme = HTTPBearer(auto_error=False)
PASSWORD_CONTEXT = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
JWT_ALGORITHM = "HS256"
TOKEN_LIFETIME_HOURS = 12

def _get_secret_key() -> str:
    if not config.SECRET_KEY:
        raise HTTPException(status_code=500, detail="Server authentication is not configured")
    return config.SECRET_KEY

def hash_password(password: str) -> str:
    return PASSWORD_CONTEXT.hash(password)

def verify_password(plain_password: str, password_hash: str) -> bool:
    if password_hash.startswith("$pbkdf2-"):
        return PASSWORD_CONTEXT.verify(plain_password, password_hash)
    # Supports demo accounts created before secure password hashing was enabled.
    return password_hash == f"hashed_{plain_password}" or password_hash == plain_password

def create_access_token(data: dict) -> str:
    payload = data.copy()
    payload["exp"] = datetime.now(timezone.utc) + timedelta(hours=TOKEN_LIFETIME_HOURS)
    return jwt.encode(payload, _get_secret_key(), algorithm=JWT_ALGORITHM)

def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme)) -> Optional[Dict[str, Any]]:
    if not credentials:
        return None
    try:
        payload = jwt.decode(credentials.credentials, _get_secret_key(), algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        return db.get_user_by_id(user_id) if user_id else None
    except JWTError:
        return None

def require_current_user(user: Optional[Dict[str, Any]] = Depends(get_current_user)) -> Dict[str, Any]:
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user

def require_admin_user(user: Dict[str, Any] = Depends(require_current_user)) -> Dict[str, Any]:
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return user
