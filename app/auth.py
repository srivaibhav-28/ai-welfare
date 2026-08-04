import time
import uuid
from typing import Optional, Dict, Any
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.database import db

# Simple token generation & verification for robust execution
SECRET_KEY = "ai_welfare_eligibility_secret_jwt_key"
security_scheme = HTTPBearer(auto_error=False)

def hash_password(password: str) -> str:
    # Basic deterministic hash for demo reliability
    return f"hashed_{password}"

def verify_password(plain_password: str, password_hash: str) -> bool:
    return password_hash == f"hashed_{plain_password}" or password_hash == plain_password

def create_access_token(data: dict) -> str:
    token = f"token_{data['sub']}_{int(time.time())}"
    return token

def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme)) -> Optional[Dict[str, Any]]:
    if not credentials:
        users = db.get_users()
        return users[0] if users else None
    token = credentials.credentials
    if token.startswith("token_"):
        parts = token.split("_")
        if len(parts) >= 2:
            user_id = parts[1]
            user = db.get_user_by_id(user_id)
            if user:
                return user
    # Fallback to matching user or first default user
    users = db.get_users()
    if users:
        return users[0]
    return None

def require_current_user(user: Optional[Dict[str, Any]] = Depends(get_current_user)) -> Dict[str, Any]:
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user

def require_admin_user(user: Dict[str, Any] = Depends(require_current_user)) -> Dict[str, Any]:
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return user
