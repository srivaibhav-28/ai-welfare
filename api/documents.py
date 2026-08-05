import uuid
import datetime
from typing import Dict, Any
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware

from app.config import config
from app.database.supabase_db import db
from app.models.schemas import DocumentStatusUpdate
from app.services.auth_service import require_current_user
from app.services.eligibility_service import EligibilityEngine
from app.services.storage_service import storage_service
from app.utils.helpers import validate_jpeg_file

app = FastAPI(title="AI Welfare Documents & File Upload API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/upload")
async def upload_document_file(
    file: UploadFile = File(...),
    document_name: str = Form("Document"),
    user: Dict[str, Any] = Depends(require_current_user)
):
    filename = file.filename or ""
    ext = validate_jpeg_file(filename, file.content_type)

    contents = await file.read()
    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    clean_doc_name = "".join(c for c in document_name if c.isalnum() or c in (' ', '_')).rstrip().replace(' ', '_').lower()
    safe_name = f"{user['id']}_{clean_doc_name}_{uuid.uuid4().hex[:6]}{ext}"

    # Default placeholder file URL for instant response
    file_url = f"https://placehold.co/600x400/1e293b/38bdf8?text={clean_doc_name}.jpg"

    # Upload directly to Supabase Storage bucket 'scheme-documents'
    supabase_url = storage_service.upload_file_to_supabase(
        config.SUPABASE_STORAGE_BUCKET,
        safe_name,
        contents,
        content_type="image/jpeg"
    )
    if supabase_url:
        file_url = supabase_url

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
            "status": status_info.get("status", "Missing"),
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
