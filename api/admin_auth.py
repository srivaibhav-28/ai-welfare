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
    """
    Surgical Admin Login Endpoint.
    Only the single configured system administrator can log in.
    Admin registration, public signup, OTP, and invite codes are disabled.
    """
    clean_email = req.email.strip().lower()
    if not authenticate_admin(clean_email, req.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Admin Credentials. Access Denied."
        )

    # Ensure single admin record exists in public.users in Supabase database
    try:
        db.ensure_single_admin()
    except Exception as e:
        print(f"[ADMIN AUTH SYNC WARNING]: {e}")
    
    token = create_access_token({
        "sub": ADMIN_USER_ID,
        "email": ADMIN_EMAIL,
        "role": "admin",
        "name": ADMIN_NAME
    })

    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": ADMIN_USER_ID,
        "name": ADMIN_NAME,
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

