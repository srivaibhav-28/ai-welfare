import uuid
from typing import Dict, Any
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware

from app.database.supabase_db import db
from app.models.schemas import UserRegister, UserLogin, TokenResponse, ChangePassword
from app.services.auth_service import (
    hash_password, verify_password, create_access_token, require_current_user
)

app = FastAPI(title="AI Welfare Auth API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/auth/register", response_model=TokenResponse)
async def register_user(req: UserRegister):
    if req.role != "citizen":
        raise HTTPException(status_code=403, detail="Admin accounts must be created by an existing administrator")
    existing = db.get_user_by_email(req.email)
    if existing:
        raise HTTPException(status_code=400, detail="User with this email already exists")

    new_user = {
        "id": f"usr-{uuid.uuid4().hex[:8]}",
        "email": req.email,
        "password_hash": hash_password(req.password),
        "name": req.name,
        "mobile_number": req.mobile_number,
        "role": req.role,
        "profile": {
            "name": req.name,
            "mobile_number": req.mobile_number,
            "age": 25,
            "gender": "Male",
            "marital_status": "Single",
            "state": "Uttar Pradesh",
            "district": "Varanasi",
            "occupation": "Self-Employed",
            "annual_income": 150000,
            "education": "Secondary",
            "caste_category": "General",
            "disability_status": False,
            "student_status": False,
            "farmer_status": False,
            "senior_citizen_status": False,
            "widow_status": False,
            "bpl_status": False,
            "aadhaar_available": True,
            "bank_account_available": True,
            "rural_urban": "Rural"
        }
    }
    db.add_user(new_user)
    token = create_access_token({"sub": new_user["id"]})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": new_user["id"],
        "name": new_user["name"],
        "email": new_user["email"],
        "mobile_number": new_user.get("mobile_number", ""),
        "role": new_user["role"]
    }

@app.post("/api/auth/login", response_model=TokenResponse)
async def login_user(req: UserLogin):
    user = db.get_user_by_email(req.email)
    if not user or not verify_password(req.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token({"sub": user["id"]})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user["id"],
        "name": user["name"],
        "email": user["email"],
        "mobile_number": user.get("mobile_number") or "",
        "role": user["role"]
    }

@app.post("/api/auth/change-password")
async def change_password(req: ChangePassword, user: Dict[str, Any] = Depends(require_current_user)):
    db_user = db.get_user_by_id(user["id"])
    if not db_user or not verify_password(req.old_password, db_user["password_hash"]):
        raise HTTPException(status_code=400, detail="Incorrect current password")
    
    new_hash = hash_password(req.new_password)
    db.update_user_password(user["id"], new_hash)
    return {"message": "Password changed successfully"}

@app.get("/api/auth/me")
async def get_me(user: Dict[str, Any] = Depends(require_current_user)):
    return user
