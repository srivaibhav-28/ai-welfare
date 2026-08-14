import uuid
import datetime
from typing import Dict, Any, List
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware

from app.database.supabase_db import db
from app.models.schemas import (
    SchemeCreate, SchemeUpdate, SchemeRuleUpdate, UserStatusUpdate,
    DocumentVerifyRequest, NotificationCreate
)
from app.services.auth_service import require_current_user, require_admin_user
from app.services.storage_service import storage_service

from pydantic import BaseModel
from app.admin_constants import ADMIN_EMAIL, ADMIN_NAME, ADMIN_USER_ID, authenticate_admin
from app.services.auth_service import create_access_token

app = FastAPI(title="AI Welfare Admin Portal API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AdminLoginRequest(BaseModel):
    email: str
    password: str

@app.post("/api/admin/login")
async def admin_login(req: AdminLoginRequest) -> Dict[str, Any]:
    clean_email = req.email.strip().lower()
    if not authenticate_admin(clean_email, req.password):
        raise HTTPException(
            status_code=401,
            detail="Invalid Admin Credentials. Access Denied."
        )

    admin_record = {
        "id": ADMIN_USER_ID,
        "email": ADMIN_EMAIL,
        "name": ADMIN_NAME,
        "mobile_number": "",
        "role": "admin",
        "is_verified": True,
        "profile": {"role": "admin"}
    }
    
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

@app.post("/api/admin/schemes")
async def admin_create_scheme(req: SchemeCreate, admin: Dict[str, Any] = Depends(require_admin_user)):
    new_scheme = req.model_dump()
    new_scheme["id"] = f"scheme-{uuid.uuid4().hex[:6]}"
    db.add_scheme(new_scheme)
    db.add_audit_log("Scheme Created", admin.get("email", "Admin"), f"Created scheme {new_scheme['name']}")
    return {"message": "Scheme created successfully", "scheme": new_scheme}

@app.put("/api/admin/schemes/{scheme_id}")
async def admin_update_scheme(scheme_id: str, req: SchemeUpdate, admin: Dict[str, Any] = Depends(require_admin_user)):
    updated = db.update_scheme(scheme_id, req.model_dump(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Scheme not found")
    db.add_audit_log("Scheme Updated", admin.get("email", "Admin"), f"Updated scheme {scheme_id}")
    return {"message": "Scheme updated successfully", "scheme": updated}

@app.delete("/api/admin/schemes/{scheme_id}")
async def admin_delete_scheme(scheme_id: str, admin: Dict[str, Any] = Depends(require_admin_user)):
    success = db.delete_scheme(scheme_id)
    if not success:
        raise HTTPException(status_code=404, detail="Scheme not found")
    db.add_audit_log("Scheme Deleted", admin.get("email", "Admin"), f"Deleted scheme {scheme_id}")
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
    db.add_audit_log("User Status Updated", admin.get("email", "Admin"), f"User {user_id} status updated to '{status_str}'")
    return {"message": f"User successfully {status_str}", "user": updated}

@app.delete("/api/admin/users/{user_id}")
async def admin_delete_user(user_id: str, admin: Dict[str, Any] = Depends(require_admin_user)):
    deleted = db.delete_user(user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")
    db.add_audit_log("User Deleted", admin.get("email", "Admin"), f"Deleted user {user_id} and associated applications and documents")
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
    db.add_audit_log("Document Verified", admin.get("email", "Admin"), f"Document '{req.document_name}' status set to '{req.status}' for user {req.user_id}")
    
    # Send Notification to User
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

@app.get("/api/admin/supabase-status")
async def admin_get_supabase_status(admin: Dict[str, Any] = Depends(require_admin_user)):
    status = storage_service.test_connection()
    status["tables"] = {
        "users": len(db.get_users()),
        "schemes": len(db.get_schemes()),
        "applications": len(db.get_applications()),
        "notifications": len(db.get_notifications())
    }
    return status

@app.get("/api/admin/dashboard")
@app.get("/api/admin/analytics")
async def admin_get_analytics(admin: Dict[str, Any] = Depends(require_admin_user)):
    users = db.fetch_rows("users") or db.get_users()
    schemes = db.fetch_rows("schemes") or db.get_schemes()
    apps = db.fetch_rows("applications") or db.get_applications()

    status_counts = {
        "Applied": 0,
        "Under Verification": 0,
        "Pending": 0,
        "Approved": 0,
        "Rejected": 0,
        "Benefits Received": 0,
        "Under Fraud Review": 0
    }
    flagged_fraud_count = 0
    for a in apps:
        st = a.get("status", "Applied")
        status_counts[st] = status_counts.get(st, 0) + 1
        if a.get("is_flagged_fraud"):
            flagged_fraud_count += 1

    category_counts = {}
    for s in schemes:
        cat = s.get("category", "General")
        category_counts[cat] = category_counts.get(cat, 0) + 1

    monthly_apps = {}
    for a in apps:
        dt_str = str(a.get("applied_date") or a.get("created_at") or "")
        if len(dt_str) >= 7:
            month_key = dt_str[:7]
            monthly_apps[month_key] = monthly_apps.get(month_key, 0) + 1

    district_counts = {}
    gender_counts = {"Male": 0, "Female": 0, "Other": 0}
    income_brackets = {"< ₹1 Lakh": 0, "₹1L - ₹2.5L": 0, "₹2.5L - ₹5L": 0, "> ₹5 Lakh": 0}

    for u in users:
        prof = u.get("profile", {}) or {}
        g = prof.get("gender", "Male")
        gender_counts[g] = gender_counts.get(g, 0) + 1
        
        dist = prof.get("district")
        if dist:
            district_counts[dist] = district_counts.get(dist, 0) + 1

        inc = prof.get("annual_income", 0)
        if inc > 0:
            if inc <= 100000:
                income_brackets["< ₹1 Lakh"] += 1
            elif inc <= 250000:
                income_brackets["₹1L - ₹2.5L"] += 1
            elif inc <= 500000:
                income_brackets["₹2.5L - ₹5L"] += 1
            else:
                income_brackets["> ₹5 Lakh"] += 1

    scheme_app_counts = {}
    for a in apps:
        s_name = a.get("scheme_name", "Unknown Scheme")
        scheme_app_counts[s_name] = scheme_app_counts.get(s_name, 0) + 1

    top_schemes = sorted(scheme_app_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    most_applied = top_schemes[0][0] if top_schemes else "N/A"

    total_apps_len = len(apps)
    pending_count = status_counts.get("Applied", 0) + status_counts.get("Under Verification", 0) + status_counts.get("Pending", 0)
    approved_count = status_counts.get("Approved", 0) + status_counts.get("Benefits Received", 0)
    rejected_count = status_counts.get("Rejected", 0)

    return {
        "total_users": len(users),
        "total_schemes": len(schemes),
        "total_applications": len(apps),
        "pending_applications": pending_count,
        "approved_applications": approved_count,
        "rejected_applications": rejected_count,
        "flagged_fraud_applications": flagged_fraud_count,
        "most_applied_scheme": most_applied,
        "approval_rate": round((approved_count / total_apps_len) * 100, 1) if total_apps_len > 0 else 0.0,
        "rejection_rate": round((rejected_count / total_apps_len) * 100, 1) if total_apps_len > 0 else 0.0,
        "application_status_distribution": status_counts,
        "scheme_category_distribution": category_counts,
        "monthly_applications": monthly_apps,
        "top_applied_schemes": dict(top_schemes),
        "applications_by_district": district_counts,
        "applications_by_gender": gender_counts,
        "applications_by_income": income_brackets,
        "recent_users": users[-5:],
        "recent_applications": apps[-5:]
    }

@app.get("/api/admin/db/{table_name}")
async def admin_get_db_table(table_name: str, admin: Dict[str, Any] = Depends(require_admin_user)):
    allowed_tables = {"users", "schemes", "applications", "user_documents"}
    if table_name not in allowed_tables:
        raise HTTPException(status_code=400, detail="Unsupported table")
    return db.fetch_rows(table_name)

@app.post("/api/admin/db/{table_name}")
async def admin_create_db_row(table_name: str, payload: Dict[str, Any], admin: Dict[str, Any] = Depends(require_admin_user)):
    allowed_tables = {"users", "schemes", "applications", "user_documents"}
    if table_name not in allowed_tables:
        raise HTTPException(status_code=400, detail="Unsupported table")
    return db.insert_row(table_name, payload)

@app.put("/api/admin/db/{table_name}/{row_id}")
async def admin_update_db_row(table_name: str, row_id: str, payload: Dict[str, Any], admin: Dict[str, Any] = Depends(require_admin_user)):
    allowed_tables = {"users", "schemes", "applications", "user_documents"}
    if table_name not in allowed_tables:
        raise HTTPException(status_code=400, detail="Unsupported table")
    return db.update_row(table_name, {"id": row_id}, payload)

@app.delete("/api/admin/db/{table_name}/{row_id}")
async def admin_delete_db_row(table_name: str, row_id: str, admin: Dict[str, Any] = Depends(require_admin_user)):
    allowed_tables = {"users", "schemes", "applications", "user_documents"}
    if table_name not in allowed_tables:
        raise HTTPException(status_code=400, detail="Unsupported table")
    deleted = db.delete_rows(table_name, {"id": row_id})
    return {"deleted": deleted}
