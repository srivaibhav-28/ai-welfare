from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from typing import Dict, Any

from app.admin_constants import (
    ADMIN_EMAIL,
    ADMIN_NAME,
    ADMIN_USER_ID,
    authenticate_admin
)
from app.services.auth_service import create_access_token
from app.database.supabase_db import db

app = FastAPI(title="AI Welfare Admin Auth API", version="2.0.0")

class AdminLoginRequest(BaseModel):
    email: str
    password: str

@app.post("/api/admin/login")
async def admin_login(req: AdminLoginRequest) -> Dict[str, Any]:
    clean_email = req.email.strip().lower()
    user = db.get_user_by_email(clean_email)
    if not user and clean_email == ADMIN_EMAIL:
        user = db.ensure_single_admin()

    if not user or user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Admin Credentials. Access Denied."
        )

    from app.services.auth_service import verify_password
    if not verify_password(req.password, user.get("password_hash", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Admin Credentials. Access Denied."
        )

    try:
        db.ensure_single_admin()
    except Exception as e:
        print(f"[ADMIN AUTH SYNC WARNING]: {e}")
    
    token = create_access_token({
        "sub": ADMIN_USER_ID,
        "email": ADMIN_EMAIL,
        "role": "admin",
        "name": user.get("name") or ADMIN_NAME
    })

    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": ADMIN_USER_ID,
        "name": user.get("name") or ADMIN_NAME,
        "email": ADMIN_EMAIL,
        "role": "admin",
        "is_verified": True
    }

@app.post("/api/admin/register")
@app.post("/api/admin/signup")
@app.post("/api/admin/invite")
@app.post("/api/admin/import")
@app.post("/api/admin/promote")
async def block_secondary_admin_creation():
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Prohibited: Single system administrator architecture enforced. Secondary admin accounts cannot be registered, invited, imported, or promoted."
    )

