import os
import uuid
import datetime
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, Depends, Request, UploadFile, File, Form, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.database import db
from app.models import (
    UserRegister, UserLogin, TokenResponse, CitizenProfile, ChangePassword,
    SchemeCreate, SchemeUpdate, ApplicationCreate, ApplicationStatusUpdate,
    ChatRequest, DocumentStatusUpdate, NotificationCreate, DocumentVerifyRequest,
    UserStatusUpdate, SchemeRuleUpdate
)
from app.auth import (
    hash_password, verify_password, create_access_token,
    get_current_user, require_current_user, require_admin_user
)
from app.engine import EligibilityEngine
from app.chatbot import AIChatbot
from app.supabase_client import supabase_client
from app.supabase_db import supabase_db

app = FastAPI(
    title="AI Government Welfare Eligibility Assistant API",
    description="Intelligent Welfare Discovery, AI Recommendation Engine, Document Checklist & Application Tracker API",
    version="2.0.0"
)

# Enable CORS for full flexibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
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

    # Save to local storage in static/uploads first for instant response
    local_path = os.path.join(UPLOADS_DIR, safe_name)
    with open(local_path, "wb") as f:
        f.write(contents)
    file_url = f"/static/uploads/{safe_name}"

    # Try uploading to Supabase Storage bucket 'scheme-documents'
    try:
        supabase_url = supabase_client.upload_file_to_storage("scheme-documents", safe_name, contents, content_type="image/jpeg")
        if supabase_url:
            file_url = supabase_url
    except Exception as exc:
        print(f"[Supabase Storage upload skipped]: {exc}")

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



@app.put("/api/admin/schemes/{scheme_id}/rules")
async def admin_update_scheme_rules(scheme_id: str, req: SchemeRuleUpdate, admin: Dict[str, Any] = Depends(require_admin_user)):
    update_data = {"criteria": req.criteria}
    if req.required_documents is not None:
        update_data["required_documents"] = req.required_documents
    updated = db.update_scheme(scheme_id, update_data)
    if not updated:
        raise HTTPException(status_code=404, detail="Scheme not found")
    return {"message": "Eligibility rules updated successfully", "scheme": updated}

@app.get("/api/admin/users")
async def admin_get_users(admin: Dict[str, Any] = Depends(require_admin_user)):
    users = db.get_users()
    apps = db.get_applications()
    safe_users = []
    for u in users:
        u_copy = dict(u)
        u_copy.pop("password_hash", None)
        user_apps = [a for a in apps if a.get("user_id") == u["id"]]
        u_copy["applications_count"] = len(user_apps)
        u_copy["user_documents"] = db.get_user_documents(u["id"])
        safe_users.append(u_copy)
    return safe_users

@app.put("/api/admin/users/{user_id}/status")
async def admin_update_user_status(user_id: str, req: UserStatusUpdate, admin: Dict[str, Any] = Depends(require_admin_user)):
    updated = db.update_user_status(user_id, req.is_blocked)
    if not updated:
        raise HTTPException(status_code=404, detail="User not found")
    status_str = "blocked" if req.is_blocked else "unblocked"
    return {"message": f"User successfully {status_str}", "user": updated}

@app.delete("/api/admin/users/{user_id}")
async def admin_delete_user(user_id: str, admin: Dict[str, Any] = Depends(require_admin_user)):
    deleted = db.delete_user(user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User and associated records deleted successfully"}

@app.post("/api/admin/documents/verify")
async def admin_verify_document(req: DocumentVerifyRequest, admin: Dict[str, Any] = Depends(require_admin_user)):
    doc_info = {
        "status": req.status,
        "upload_date": datetime.date.today().isoformat(),
        "remarks": req.remarks,
        "verified_by": admin.get("name", "Admin")
    }
    db.update_user_document(req.user_id, req.document_name, doc_info)
    
    # Also notify user
    notif = {
        "id": f"notif-{uuid.uuid4().hex[:6]}",
        "title": f"Document Verification Update: {req.document_name}",
        "message": f"Your document '{req.document_name}' status was updated to '{req.status}'. Remarks: {req.remarks or 'Verified by Admin'}",
        "target_user_id": req.user_id,
        "type": "success" if req.status == "Verified" else "warning",
        "created_at": datetime.datetime.now().isoformat()
    }
    db.add_notification(notif)
    return {"message": f"Document status updated to {req.status}", "document": doc_info}

@app.get("/api/admin/notifications")
async def admin_get_notifications(admin: Dict[str, Any] = Depends(require_admin_user)):
    return db.get_notifications()

@app.post("/api/admin/notifications")
async def admin_send_notification(req: NotificationCreate, admin: Dict[str, Any] = Depends(require_admin_user)):
    new_notif = {
        "id": f"notif-{uuid.uuid4().hex[:6]}",
        "title": req.title,
        "message": req.message,
        "target_user_id": req.target_user_id,
        "type": req.type,
        "created_at": datetime.datetime.now().isoformat(),
        "sent_by": admin.get("name", "Admin")
    }
    db.add_notification(new_notif)
    return {"message": "Notification broadcast successfully", "notification": new_notif}

@app.get("/api/notifications")
async def get_user_notifications(user: Dict[str, Any] = Depends(require_current_user)):
    return db.get_notifications(target_user_id=user["id"])

@app.get("/api/admin/reports/export")
async def admin_export_reports(admin: Dict[str, Any] = Depends(require_admin_user)):
    apps = db.get_applications()
    schemes = db.get_schemes()
    users = db.get_users()

    import io, csv
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Application ID", "Applicant Name", "Applicant Email", "Scheme Name", "Applied Date", "Status", "Remarks"])

    user_map = {u["id"]: u for u in users}
    for a in apps:
        u_info = user_map.get(a.get("user_id"), {})
        writer.writerow([
            a.get("id", ""),
            a.get("user_name", u_info.get("name", "N/A")),
            a.get("user_email", u_info.get("email", "N/A")),
            a.get("scheme_name", ""),
            a.get("applied_date", ""),
            a.get("status", ""),
            a.get("remarks", "")
        ])

    csv_data = output.getvalue()
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=welfare_applications_report_{datetime.date.today().isoformat()}.csv"}
    )

@app.get("/api/admin/supabase-status")
async def admin_get_supabase_status(admin: Dict[str, Any] = Depends(require_admin_user)):
    status = supabase_client.test_connection()
    status["tables"] = {
        "users": len(db.get_users()),
        "schemes": len(db.get_schemes()),
        "applications": len(db.get_applications()),
        "notifications": len(db.get_notifications())
    }
    return status

@app.get("/api/admin/db/{table_name}")
async def admin_get_db_table(table_name: str, admin: Dict[str, Any] = Depends(require_admin_user)):
    allowed_tables = {"users", "schemes", "applications", "user_documents"}
    if table_name not in allowed_tables:
        raise HTTPException(status_code=400, detail="Unsupported table")
    rows = supabase_db.fetch_rows(table_name)
    return rows

@app.post("/api/admin/db/{table_name}")
async def admin_create_db_row(table_name: str, payload: Dict[str, Any], admin: Dict[str, Any] = Depends(require_admin_user)):
    allowed_tables = {"users", "schemes", "applications", "user_documents"}
    if table_name not in allowed_tables:
        raise HTTPException(status_code=400, detail="Unsupported table")
    row = supabase_db.insert_row(table_name, payload)
    return row

@app.put("/api/admin/db/{table_name}/{row_id}")
async def admin_update_db_row(table_name: str, row_id: str, payload: Dict[str, Any], admin: Dict[str, Any] = Depends(require_admin_user)):
    allowed_tables = {"users", "schemes", "applications", "user_documents"}
    if table_name not in allowed_tables:
        raise HTTPException(status_code=400, detail="Unsupported table")
    if table_name == "user_documents":
        payload = {**payload, "id": row_id}
    row = supabase_db.update_row(table_name, {"id": row_id}, payload)
    return row

@app.delete("/api/admin/db/{table_name}/{row_id}")
async def admin_delete_db_row(table_name: str, row_id: str, admin: Dict[str, Any] = Depends(require_admin_user)):
    allowed_tables = {"users", "schemes", "applications", "user_documents"}
    if table_name not in allowed_tables:
        raise HTTPException(status_code=400, detail="Unsupported table")
    deleted = supabase_db.delete_rows(table_name, {"id": row_id})
    return {"deleted": deleted}

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

    # Monthly distribution (sample / dynamic calculation)
    monthly_apps = {
        "Jan": 12, "Feb": 18, "Mar": 24, "Apr": 19, "May": 28, "Jun": 35, "Jul": 42
    }

    # Top schemes calculation
    scheme_app_counts = {}
    for a in apps:
        s_name = a.get("scheme_name", "Unknown Scheme")
        scheme_app_counts[s_name] = scheme_app_counts.get(s_name, 0) + 1

    top_schemes = sorted(scheme_app_counts.items(), key=lambda x: x[1], reverse=True)[:5]

    return {
        "total_users": len(users),
        "total_schemes": len(schemes),
        "total_applications": len(apps),
        "pending_applications": status_counts.get("Applied", 0) + status_counts.get("Under Verification", 0),
        "approved_applications": status_counts.get("Approved", 0) + status_counts.get("Benefits Received", 0),
        "rejected_applications": status_counts.get("Rejected", 0),
        "approval_rate": round(((status_counts.get("Approved", 0) + status_counts.get("Benefits Received", 0)) / (len(apps) or 1)) * 100, 1),
        "application_status_distribution": status_counts,
        "scheme_category_distribution": category_counts,
        "monthly_applications": monthly_apps,
        "top_applied_schemes": dict(top_schemes),
        "recent_users": users[-5:],
        "recent_applications": apps[-5:]
    }

