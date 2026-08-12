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

def check_profile_completion(p: Dict[str, Any]) -> bool:
    if not p:
        return False
    a_num = str(p.get("aadhaar_number", "")).strip()
    dob = str(p.get("dob", "")).strip()
    dist = str(p.get("district", "")).strip()
    pin = str(p.get("pincode", "")).strip()
    bank = str(p.get("bank_account_number", "")).strip()
    
    has_valid_aadhaar = len(a_num) == 12 and a_num.isdigit()
    has_valid_pincode = len(pin) == 6 and pin.isdigit()
    has_dob = len(dob) > 0
    has_district = len(dist) > 0
    has_bank = len(bank) > 0
    
    return bool(p.get("profile_completed", False) and has_valid_aadhaar and has_valid_pincode and has_dob and has_district and has_bank)

@app.get("/api/profile")
async def get_profile(user: Dict[str, Any] = Depends(require_current_user)):
    prof = user.get("profile", {}) or {}
    if not prof.get("name"):
        prof["name"] = user.get("name", "")
    if not prof.get("mobile_number"):
        prof["mobile_number"] = user.get("mobile_number", "")
    prof["profile_completed"] = check_profile_completion(prof)
    return prof

@app.post("/api/profile")
async def update_profile(profile_data: CitizenProfile, user: Dict[str, Any] = Depends(require_current_user)):
    pdict = profile_data.model_dump()
    
    a_num = str(pdict.get("aadhaar_number", "")).strip()
    dob = str(pdict.get("dob", "")).strip()
    dist = str(pdict.get("district", "")).strip()
    pin = str(pdict.get("pincode", "")).strip()
    bank = str(pdict.get("bank_account_number", "")).strip()

    is_complete = bool(len(a_num) == 12 and a_num.isdigit() and len(pin) == 6 and pin.isdigit() and dob and dist and bank)
    pdict["profile_completed"] = is_complete

    updated = db.update_user_profile(user["id"], pdict)
    return {
        "message": "Profile updated successfully" if is_complete else "Profile saved as draft (incomplete required fields)",
        "profile_completed": is_complete,
        "profile": updated.get("profile", pdict) if (isinstance(updated, dict) and "profile" in updated) else pdict
    }

@app.get("/api/users")
async def get_users(admin: Dict[str, Any] = Depends(require_admin_user)):
    return db.get_users()
