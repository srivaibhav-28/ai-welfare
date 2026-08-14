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

    # Ensure single admin record exists in public.users / db cache
    admin_record = {
        "id": ADMIN_USER_ID,
        "email": ADMIN_EMAIL,
        "name": ADMIN_NAME,
        "mobile_number": "",
        "role": "admin",
        "is_verified": True,
        "profile": {"role": "admin"}
    }
    
    # Store or update in database
    db.add_user(admin_record)

    token = create_access_token({"sub": ADMIN_USER_ID, "role": "admin"})

    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": ADMIN_USER_ID,
        "name": ADMIN_NAME,
        "email": ADMIN_EMAIL,
        "role": "admin",
        "is_verified": True
    }
