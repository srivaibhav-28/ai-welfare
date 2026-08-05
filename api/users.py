from typing import Dict, Any
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware

from app.database.supabase_db import db
from app.models.schemas import CitizenProfile
from app.services.auth_service import require_current_user, require_admin_user

app = FastAPI(title="AI Welfare Users API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/profile")
async def get_profile(user: Dict[str, Any] = Depends(require_current_user)):
    prof = user.get("profile", {})
    if not prof.get("name"):
        prof["name"] = user.get("name", "")
    if not prof.get("mobile_number"):
        prof["mobile_number"] = user.get("mobile_number", "")
    return prof

@app.post("/api/profile")
async def update_profile(profile_data: CitizenProfile, user: Dict[str, Any] = Depends(require_current_user)):
    updated = db.update_user_profile(user["id"], profile_data.model_dump())
    return {"message": "Profile updated successfully", "profile": updated["profile"] if updated else profile_data.model_dump()}

@app.get("/api/users")
async def get_users(admin: Dict[str, Any] = Depends(require_admin_user)):
    return db.get_users()
