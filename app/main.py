import os
import uuid
import datetime
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, Depends, Request, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.database import db
from app.models import (
    UserRegister, UserLogin, TokenResponse, CitizenProfile, ChangePassword,
    SchemeCreate, SchemeUpdate, ApplicationCreate, ApplicationStatusUpdate,
    ChatRequest, DocumentStatusUpdate
)
from app.auth import (
    hash_password, verify_password, create_access_token,
    get_current_user, require_current_user, require_admin_user
)
from app.engine import EligibilityEngine
from app.chatbot import AIChatbot
from app.supabase_client import supabase_client

app = FastAPI(
    title="AI Government Welfare Eligibility Assistant API",
    description="Intelligent Welfare Discovery, AI Recommendation Engine, Document Checklist & Application Tracker API",
    version="2.0.0"
)

# Enable CORS for full flexibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static file serving
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, "static")
UPLOADS_DIR = os.path.join(STATIC_DIR, "uploads")

os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(UPLOADS_DIR, exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/", response_class=HTMLResponse)
async def serve_homepage():
    index_candidates = [
        os.path.join(BASE_DIR, "index.html"),
        os.path.join(STATIC_DIR, "index.html")
    ]
    for index_path in index_candidates:
        if os.path.exists(index_path):
            with open(index_path, "r", encoding="utf-8") as f:
                return f.read()
    return "<h1>AI Government Welfare Eligibility Assistant Server Running</h1>"

# AUTHENTICATION ENDPOINTS
@app.post("/api/auth/register", response_model=TokenResponse)
async def register_user(req: UserRegister):
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
        "mobile_number": user.get("mobile_number", ""),
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

# USER PROFILE ENDPOINTS
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
    return {"message": "Profile updated successfully", "profile": updated["profile"]}

# SCHEME ENDPOINTS
@app.get("/api/schemes")
async def get_all_schemes():
    return db.get_schemes()

@app.get("/api/schemes/{scheme_id}")
async def get_scheme_details(scheme_id: str):
    scheme = db.get_scheme_by_id(scheme_id)
    if not scheme:
        raise HTTPException(status_code=404, detail="Scheme not found")
    return scheme

# AI RECOMMENDATION ENGINE ENDPOINT
@app.post("/api/evaluate")
async def evaluate_eligibility(profile: CitizenProfile):
    schemes = db.get_schemes()
    result = EligibilityEngine.analyze_all(profile.model_dump(), schemes)
    return result

# FILE UPLOAD ENDPOINT (STRICT JPEG RESTRICTION)
@app.post("/api/upload")
async def upload_document_file(
    file: UploadFile = File(...),
    document_name: str = Form("Document"),
    user: Dict[str, Any] = Depends(require_current_user)
):
    filename = file.filename or ""
    ext = os.path.splitext(filename)[1].lower()
    
    # Strict JPEG validation (.jpg, .jpeg)
    allowed_exts = [".jpg", ".jpeg"]
    is_jpeg_ext = ext in allowed_exts
    is_jpeg_mime = file.content_type and "jpeg" in file.content_type.lower() or "jpg" in file.content_type.lower()
    
    if not (is_jpeg_ext or is_jpeg_mime):
        raise HTTPException(
            status_code=400,
            detail="Invalid file format! Only JPEG (.jpg / .jpeg) documents are allowed."
        )

    contents = await file.read()
    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    clean_doc_name = "".join(c for c in document_name if c.isalnum() or c in (' ', '_')).rstrip().replace(' ', '_').lower()
    safe_name = f"{user['id']}_{clean_doc_name}_{uuid.uuid4().hex[:6]}{ext if ext in allowed_exts else '.jpg'}"

    # Try uploading to Supabase Storage bucket 'scheme-documents'
    supabase_url = supabase_client.upload_file_to_storage("scheme-documents", safe_name, contents, content_type="image/jpeg")

    if supabase_url:
        file_url = supabase_url
    else:
        # Fallback to local storage in static/uploads
        local_path = os.path.join(UPLOADS_DIR, safe_name)
        with open(local_path, "wb") as f:
            f.write(contents)
        file_url = f"/static/uploads/{safe_name}"

    # Update user documents state
    doc_info = {
        "status": "Uploaded",
        "upload_date": datetime.date.today().isoformat(),
        "file_name": filename,
        "file_url": file_url
    }
    db.update_user_document(user["id"], document_name, doc_info)

    return {
        "message": f"Successfully uploaded {document_name} in JPEG format",
        "document_name": document_name,
        "file_name": filename,
        "file_url": file_url
    }

# DOCUMENT CHECKLIST ENDPOINTS
@app.get("/api/documents")
async def get_documents(user: Dict[str, Any] = Depends(require_current_user)):
    user_docs = db.get_user_documents(user["id"])
    profile = user.get("profile", {})
    schemes = db.get_schemes()
    eval_result = EligibilityEngine.analyze_all(profile, schemes)
    required_set = eval_result["smart_document_checklist"]

    checklist = []
    for doc in required_set:
        status_info = user_docs.get(doc, {"status": "Missing", "upload_date": None, "file_name": None, "file_url": None})
        checklist.append({
            "document_name": doc,
            "status": status_info["status"],
            "upload_date": status_info.get("upload_date"),
            "file_name": status_info.get("file_name"),
            "file_url": status_info.get("file_url")
        })
    return checklist

@app.post("/api/documents/status")
async def update_doc_status(req: DocumentStatusUpdate, user: Dict[str, Any] = Depends(require_current_user)):
    doc_info = {
        "status": req.status,
        "upload_date": datetime.date.today().isoformat(),
        "file_name": req.file_name or f"{req.document_name.lower().replace(' ', '_')}.jpg"
    }
    db.update_user_document(user["id"], req.document_name, doc_info)
    return {"message": "Document status updated", "document": doc_info}

# APPLICATION TRACKER ENDPOINTS
@app.get("/api/applications")
async def get_applications(user: Dict[str, Any] = Depends(require_current_user)):
    if user.get("role") == "admin":
        return db.get_applications()
    return db.get_applications(user_id=user["id"])

@app.post("/api/applications/apply")
async def apply_for_scheme(req: ApplicationCreate, user: Dict[str, Any] = Depends(require_current_user)):
    scheme = db.get_scheme_by_id(req.scheme_id)
    if not scheme:
        raise HTTPException(status_code=404, detail="Scheme not found")

    existing_apps = db.get_applications(user_id=user["id"])
    for app_item in existing_apps:
        if app_item["scheme_id"] == req.scheme_id:
            raise HTTPException(status_code=400, detail="You have already applied for this scheme.")

    # Validate that all required scheme documents are present
    req_docs = scheme.get("required_documents", [])
    user_docs = db.get_user_documents(user["id"])
    missing_docs = []
    
    for d in req_docs:
        doc_meta = user_docs.get(d)
        if not doc_meta or doc_meta.get("status") not in ["Uploaded", "Verified"] and not (req.uploaded_documents and d in req.uploaded_documents):
            missing_docs.append(d)

    if missing_docs:
        raise HTTPException(
            status_code=400,
            detail=f"Please upload all required JPEG documents before submitting: {', '.join(missing_docs)}"
        )

    new_app = {
        "id": f"app-{uuid.uuid4().hex[:6]}",
        "user_id": user["id"],
        "user_name": user.get("name", "Citizen"),
        "user_email": user.get("email", ""),
        "scheme_id": scheme["id"],
        "scheme_name": scheme["name"],
        "status": "Applied",
        "applied_date": datetime.date.today().isoformat(),
        "uploaded_documents": req.uploaded_documents or {d: user_docs.get(d, {}).get("file_name", "document.jpg") for d in req_docs},
        "remarks": "Application submitted with verified JPEG documents."
    }
    db.add_application(new_app)
    return {"message": f"Successfully Applied for {scheme['name']}", "application": new_app}

@app.put("/api/applications/{app_id}/status")
async def update_app_status(app_id: str, req: ApplicationStatusUpdate, admin: Dict[str, Any] = Depends(require_admin_user)):
    updated = db.update_application_status(app_id, req.status, req.remarks)
    if not updated:
        raise HTTPException(status_code=404, detail="Application not found")
    return {"message": "Application status updated", "application": updated}

# CONVERSATIONAL AI CHATBOT ENDPOINT
@app.post("/api/chat")
async def chat_with_assistant(req: ChatRequest):
    res = AIChatbot.generate_response(req.message, language=req.language, profile_data=req.profile_data)
    return res

# ADMIN MANAGEMENT ENDPOINTS
@app.post("/api/admin/schemes")
async def admin_create_scheme(req: SchemeCreate, admin: Dict[str, Any] = Depends(require_admin_user)):
    new_scheme = req.model_dump()
    new_scheme["id"] = f"scheme-{uuid.uuid4().hex[:6]}"
    db.add_scheme(new_scheme)
    return {"message": "Scheme created successfully", "scheme": new_scheme}

@app.put("/api/admin/schemes/{scheme_id}")
async def admin_update_scheme(scheme_id: str, req: SchemeUpdate, admin: Dict[str, Any] = Depends(require_admin_user)):
    updated = db.update_scheme(scheme_id, req.model_dump(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Scheme not found")
    return {"message": "Scheme updated successfully", "scheme": updated}

@app.delete("/api/admin/schemes/{scheme_id}")
async def admin_delete_scheme(scheme_id: str, admin: Dict[str, Any] = Depends(require_admin_user)):
    success = db.delete_scheme(scheme_id)
    if not success:
        raise HTTPException(status_code=404, detail="Scheme not found")
    return {"message": "Scheme deleted successfully"}

@app.get("/api/admin/users")
async def admin_get_users(admin: Dict[str, Any] = Depends(require_admin_user)):
    users = db.get_users()
    # Mask password hashes
    safe_users = []
    for u in users:
        u_copy = dict(u)
        u_copy.pop("password_hash", None)
        safe_users.append(u_copy)
    return safe_users

@app.get("/api/admin/analytics")
async def admin_get_analytics(admin: Dict[str, Any] = Depends(require_admin_user)):
    schemes = db.get_schemes()
    users = db.get_users()
    apps = db.get_applications()

    status_counts = {
        "Applied": 0,
        "Under Verification": 0,
        "Approved": 0,
        "Rejected": 0,
        "Benefits Received": 0
    }
    for a in apps:
        st = a.get("status", "Applied")
        status_counts[st] = status_counts.get(st, 0) + 1

    category_counts = {}
    for s in schemes:
        cat = s.get("category", "General")
        category_counts[cat] = category_counts.get(cat, 0) + 1

    return {
        "total_users": len(users),
        "total_schemes": len(schemes),
        "total_applications": len(apps),
        "application_status_distribution": status_counts,
        "scheme_category_distribution": category_counts
    }
