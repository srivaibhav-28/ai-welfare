import uuid
import datetime
from typing import Dict, Any
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware

from app.database.supabase_db import db
from app.models.schemas import ApplicationCreate, ApplicationStatusUpdate
from app.services.auth_service import require_current_user, require_admin_user

app = FastAPI(title="AI Welfare Applications API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

    # Validate required documents
    req_docs = scheme.get("required_documents", [])
    user_docs = db.get_user_documents(user["id"])
    missing_docs = []
    
    for d in req_docs:
        doc_meta = user_docs.get(d)
        is_in_user_docs = doc_meta and doc_meta.get("status") in ["Uploaded", "Verified"]
        is_in_req_uploads = bool(req.uploaded_documents and req.uploaded_documents.get(d))
        if not (is_in_user_docs or is_in_req_uploads):
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
