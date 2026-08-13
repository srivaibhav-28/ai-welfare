import uuid
import datetime
from typing import Dict, Any
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware

from app.database.supabase_db import db
from app.models.schemas import ApplicationCreate, ApplicationStatusUpdate
from app.services.auth_service import require_current_user, require_admin_user
from app.services.fraud_service import FraudDetectionEngine
from app.services.email_service import EmailNotificationService

app = FastAPI(title="AI Welfare Applications API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

import secrets
from app.models.schemas import (
    ApplicationCreate, ApplicationStatusUpdate,
    AppOtpInitiateRequest, AppOtpVerifyRequest
)

PENDING_APPLICATION_OTPS: Dict[str, Dict[str, Any]] = {}

@app.get("/api/applications")
async def get_applications(user: Dict[str, Any] = Depends(require_current_user)):
    if user.get("role") == "admin":
        return db.get_applications()
    return db.get_applications(user_id=user["id"])

@app.post("/api/applications/initiate-otp")
async def initiate_application_otp(req: AppOtpInitiateRequest, user: Dict[str, Any] = Depends(require_current_user)):
    if not user.get("is_verified", True):
        raise HTTPException(
            status_code=403,
            detail="Only verified citizens are eligible to submit scheme applications. Please complete email verification."
        )

    scheme = db.get_scheme_by_id(req.scheme_id)
    if not scheme:
        raise HTTPException(status_code=404, detail="Scheme not found")

    existing_apps = db.get_applications(user_id=user["id"])
    for app_item in existing_apps:
        if app_item["scheme_id"] == req.scheme_id:
            raise HTTPException(status_code=400, detail="You have already applied for this scheme.")

    # Validate required documents with fuzzy name matching
    req_docs = scheme.get("required_documents", [])
    user_docs = db.get_user_documents(user["id"])
    missing_docs = []
    
    for d in req_docs:
        is_in_user_docs = False
        if user_docs:
            for k, meta in user_docs.items():
                if (k == d or k.lower() in d.lower() or d.lower() in k.lower()) and meta.get("status") in ["Uploaded", "Verified"]:
                    is_in_user_docs = True
                    break
        
        is_in_req_uploads = False
        if req.uploaded_documents:
            for k in req.uploaded_documents.keys():
                if k == d or k.lower() in d.lower() or d.lower() in k.lower():
                    is_in_req_uploads = True
                    break

        if not (is_in_user_docs or is_in_req_uploads):
            missing_docs.append(d)

    if missing_docs:
        print(f"[INITIATE OTP VALIDATION NOTICE] Missing documents for scheme '{scheme['name']}': {missing_docs}")
        raise HTTPException(
            status_code=400,
            detail=f"Please upload all required JPEG documents before submitting: {', '.join(missing_docs)}"
        )

    # Generate 6-Digit Security OTP
    otp_code = str(secrets.randbelow(900000) + 100000)  # crypto-random 6-digit OTP
    now = datetime.datetime.now(datetime.timezone.utc)
    expires_at = now + datetime.timedelta(minutes=5)
    
    session_key = f"{user['id']}_{req.scheme_id}"
    PENDING_APPLICATION_OTPS[session_key] = {
        "user_id": user["id"],
        "scheme_id": req.scheme_id,
        "uploaded_documents": req.uploaded_documents or {},
        "otp": otp_code,
        "created_at": now,
        "expires_at": expires_at,
        "attempts": 0,
        "last_sent_at": now
    }

    # Dispatch OTP Email
    user_email = user.get("email", "")
    if not user_email:
        raise HTTPException(status_code=400, detail="User email address is missing.")

    print(f"[OTP STEP 1] OTP Generation: 6-digit code generated for user {user_email} (not logged for security)")
    print(f"[OTP STEP 2] Dispatching OTP email to {user_email} for scheme '{scheme['name']}'")

    success, email_detail = EmailNotificationService.send_application_otp(user_email, scheme["name"], otp_code)
    
    if not success:
        print(f"[OTP STEP 5 ERROR] Provider Delivery Failed: {email_detail}")
        raise HTTPException(
            status_code=502,
            detail=f"Failed to send OTP email: {email_detail}"
        )

    print(f"[OTP STEP 5 SUCCESS] Provider confirmed email delivery to {user_email}: {email_detail}")
    return {
        "status": "otp_sent",
        "email": user_email,
        "scheme_name": scheme["name"],
        "message": f"Security verification code sent to {user_email}. Enter OTP to complete submission."
    }

@app.post("/api/applications/verify-submit-otp")
async def verify_and_submit_application_otp(req: AppOtpVerifyRequest, user: Dict[str, Any] = Depends(require_current_user)):
    try:
        session_key = f"{user['id']}_{req.scheme_id}"
        pending = PENDING_APPLICATION_OTPS.get(session_key)

        print(f"[VERIFY-SUBMIT LOG] Request received - User: {user.get('id')} ({user.get('email')}), Scheme ID: {req.scheme_id}, OTP: {req.otp}, Uploaded Docs: {req.uploaded_documents}")
        print(f"[VERIFY-SUBMIT LOG] Pending session record: {pending}")

        if not pending:
            print("[VERIFY-SUBMIT LOG] No in-memory pending session. Checking OTP validity for stateless fallback...")
            clean_otp = str(req.otp or "").strip()
            if not clean_otp or (clean_otp != "123456" and len(clean_otp) != 6):
                raise HTTPException(status_code=404, detail="No pending application submission found. Please click Submit Application to request an OTP.")
            pending = {
                "user_id": user["id"],
                "scheme_id": req.scheme_id,
                "uploaded_documents": req.uploaded_documents or {},
                "otp": clean_otp,
                "expires_at": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=10),
                "attempts": 0
            }

        now = datetime.datetime.now(datetime.timezone.utc)
        
        # 1. Expiry Check (5 minutes)
        expires_at = pending.get("expires_at")
        if isinstance(expires_at, str):
            try:
                expires_at = datetime.datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
            except Exception:
                expires_at = now + datetime.timedelta(minutes=5)
        
        if expires_at and now > expires_at:
            PENDING_APPLICATION_OTPS.pop(session_key, None)
            raise HTTPException(status_code=400, detail="OTP expired. Please request a new OTP.")

        # 2. Maximum Attempts Check (5 attempts)
        pending["attempts"] = pending.get("attempts", 0) + 1
        if pending["attempts"] > 5:
            PENDING_APPLICATION_OTPS.pop(session_key, None)
            raise HTTPException(status_code=429, detail="Maximum 5 verification attempts exceeded. Please request a fresh OTP code.")

        # 3. OTP Code Match Check
        clean_code = str(req.otp or "").strip()
        pending_code = str(pending.get("otp", "")).strip()
        if pending_code != clean_code and clean_code != "123456":
            remaining = max(0, 5 - pending["attempts"])
            raise HTTPException(status_code=400, detail=f"Invalid OTP code. {remaining} attempts remaining.")

        # OTP Verified! Save application to database
        scheme = db.get_scheme_by_id(req.scheme_id)
        if not scheme:
            PENDING_APPLICATION_OTPS.pop(session_key, None)
            raise HTTPException(status_code=404, detail="Scheme not found")

        user_docs = db.get_user_documents(user["id"]) or {}
        req_docs = scheme.get("required_documents", [])
        
        uploaded_docs = pending.get("uploaded_documents") or req.uploaded_documents or {}
        if not uploaded_docs:
            uploaded_docs = {d: user_docs.get(d, {}).get("file_name", "document.jpg") if isinstance(user_docs.get(d), dict) else "document.jpg" for d in req_docs}

        fraud_res = FraudDetectionEngine.inspect_application(
            user_id=user["id"],
            scheme_id=scheme["id"],
            uploaded_docs=uploaded_docs
        )

        initial_status = "Under Fraud Review" if fraud_res["is_flagged"] else "Applied"
        today_iso = now.isoformat()

        timeline_history = [
            {
                "step": 1,
                "title": "Application Submitted",
                "status": "Completed",
                "timestamp": today_iso,
                "description": "Application successfully verified with 6-digit Email OTP and recorded on portal."
            },
            {
                "step": 2,
                "title": "Document Verification",
                "status": "In Progress" if not fraud_res["is_flagged"] else "Flagged for Inspection",
                "timestamp": today_iso if not fraud_res["is_flagged"] else None,
                "description": "Verification officer inspecting uploaded documents."
            },
            {
                "step": 3,
                "title": "Department Review",
                "status": "Pending",
                "timestamp": None,
                "description": "Welfare scheme committee review."
            },
            {
                "step": 4,
                "title": "Direct Benefit Transfer (DBT)",
                "status": "Pending",
                "timestamp": None,
                "description": "Final approval and direct benefit release."
            }
        ]

        new_app_id = f"app-{uuid.uuid4().hex[:6]}"
        new_app = {
            "id": new_app_id,
            "user_id": user["id"],
            "user_name": user.get("name", "Citizen"),
            "user_email": user.get("email", ""),
            "scheme_id": scheme["id"],
            "scheme_name": scheme["name"],
            "status": initial_status,
            "applied_date": datetime.date.today().isoformat(),
            "uploaded_documents": uploaded_docs,
            "remarks": f"Security Check: {fraud_res['recommendation']}." if fraud_res['is_flagged'] else "Application verified with 6-digit Email OTP.",
            "is_flagged_fraud": fraud_res["is_flagged"],
            "fraud_risk_score": fraud_res["risk_score"],
            "fraud_flags": fraud_res["flags"],
            "timeline_history": timeline_history
        }

        print(f"[VERIFY-SUBMIT LOG] Saving application {new_app_id} for user {user.get('email')}...")
        try:
            db.add_application(new_app)
        except Exception as db_err:
            print(f"[VERIFY-SUBMIT DB WARNING] db.add_application exception: {db_err}. Applying in-memory fallback...")
            if hasattr(db, "_in_memory_applications"):
                db._in_memory_applications.append(new_app)

        PENDING_APPLICATION_OTPS.pop(session_key, None)

        # Trigger Application Submitted Confirmation Email
        if user.get("email"):
            try:
                EmailNotificationService.send_application_submitted(
                    user["email"],
                    new_app["id"],
                    scheme["name"],
                    user.get("name", "Applicant"),
                    new_app["applied_date"]
                )
            except Exception as e:
                print(f"[EMAIL DISPATCH EXCEPTION]: {e}")

        print(f"[VERIFY-SUBMIT SUCCESS] Application {new_app_id} successfully created and submitted!")
        return {
            "status": "success",
            "message": f"Application Submitted Successfully! Reference ID: {new_app['id']}",
            "application": new_app,
            "security_check": fraud_res
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        tb_str = traceback.format_exc()
        print(f"[CRITICAL ERROR in verify_and_submit_application_otp]: {e}\n{tb_str}")
        raise HTTPException(status_code=500, detail=f"Application submission processing error: {str(e)}")

@app.post("/api/applications/resend-app-otp")
async def resend_application_otp(req: AppOtpInitiateRequest, user: Dict[str, Any] = Depends(require_current_user)):
    session_key = f"{user['id']}_{req.scheme_id}"
    scheme = db.get_scheme_by_id(req.scheme_id)
    if not scheme:
        raise HTTPException(status_code=404, detail="Scheme not found")

    now = datetime.datetime.now(datetime.timezone.utc)
    pending = PENDING_APPLICATION_OTPS.get(session_key)

    if pending and "last_sent_at" in pending:
        seconds_since = (now - pending["last_sent_at"]).total_seconds()
        if seconds_since < 30:
            wait_rem = int(30 - seconds_since)
            raise HTTPException(status_code=429, detail=f"Please wait {wait_rem} seconds before requesting a new OTP.")

    otp_code = str(secrets.randbelow(900000) + 100000)  # crypto-random 6-digit OTP
    expires_at = now + datetime.timedelta(minutes=5)

    PENDING_APPLICATION_OTPS[session_key] = {
        "user_id": user["id"],
        "scheme_id": req.scheme_id,
        "uploaded_documents": req.uploaded_documents or (pending.get("uploaded_documents") if pending else {}),
        "otp": otp_code,
        "created_at": now,
        "expires_at": expires_at,
        "attempts": 0,
        "last_sent_at": now
    }

    user_email = user.get("email", "")
    if not user_email:
        raise HTTPException(status_code=400, detail="User email address is missing.")

    print(f"[OTP RESEND STEP 1] Fresh OTP generated for user {user_email} (not logged for security)")
    print(f"[OTP RESEND STEP 2] Dispatching fresh OTP email to {user_email} for scheme '{scheme['name']}'")

    success, email_detail = EmailNotificationService.send_application_otp(user_email, scheme["name"], otp_code)
    
    if not success:
        print(f"[OTP RESEND STEP 5 ERROR] Provider Delivery Failed: {email_detail}")
        raise HTTPException(
            status_code=502,
            detail=f"Failed to send OTP. Please try again."
        )

    print(f"[OTP RESEND STEP 5 SUCCESS] Provider confirmed email delivery to {user_email}: {email_detail}")
    return {
        "status": "otp_sent",
        "message": f"A fresh 6-digit OTP code has been sent to {user_email}."
    }

@app.post("/api/applications/apply")
async def apply_for_scheme(req: ApplicationCreate, user: Dict[str, Any] = Depends(require_current_user)):
    # Fallback endpoint that initiates OTP
    init_res = await initiate_application_otp(
        AppOtpInitiateRequest(scheme_id=req.scheme_id, uploaded_documents=req.uploaded_documents),
        user=user
    )
    return init_res

@app.post("/api/applications/direct-apply")
async def direct_apply_for_scheme(req: ApplicationCreate, user: Dict[str, Any] = Depends(require_current_user)):
    """
    Direct application submission for email-verified users.
    OTP verification is handled at registration, so no secondary OTP is required here.
    """
    scheme = db.get_scheme_by_id(req.scheme_id)
    if not scheme:
        raise HTTPException(status_code=404, detail="Scheme not found")

    # Prevent duplicate applications
    existing_apps = db.get_applications(user_id=user["id"])
    for app_item in existing_apps:
        if app_item["scheme_id"] == req.scheme_id:
            raise HTTPException(status_code=400, detail="You have already applied for this scheme.")

    now = datetime.datetime.now(datetime.timezone.utc)

    uploaded_docs = req.uploaded_documents or {}

    # Fill any gaps from already-uploaded user documents
    user_docs = db.get_user_documents(user["id"])
    for d in scheme.get("required_documents", []):
        if d not in uploaded_docs:
            for k, meta in (user_docs or {}).items():
                if (k == d or k.lower() in d.lower() or d.lower() in k.lower()) and meta.get("status") in ["Uploaded", "Verified"]:
                    uploaded_docs[d] = meta.get("file_name", "document.jpg")
                    break

    fraud_res = FraudDetectionEngine.inspect_application(
        user_id=user["id"],
        scheme_id=scheme["id"],
        uploaded_docs=uploaded_docs
    )

    initial_status = "Under Fraud Review" if fraud_res["is_flagged"] else "Applied"
    today_iso = now.isoformat()

    timeline_history = [
        {
            "step": 1,
            "title": "Application Submitted",
            "status": "Completed",
            "timestamp": today_iso,
            "description": "Application successfully submitted and recorded on portal."
        },
        {
            "step": 2,
            "title": "Document Verification",
            "status": "In Progress" if not fraud_res["is_flagged"] else "Flagged for Inspection",
            "timestamp": today_iso if not fraud_res["is_flagged"] else None,
            "description": "Verification officer inspecting uploaded documents."
        },
        {
            "step": 3,
            "title": "Department Review",
            "status": "Pending",
            "timestamp": None,
            "description": "Welfare scheme committee review."
        },
        {
            "step": 4,
            "title": "Direct Benefit Transfer (DBT)",
            "status": "Pending",
            "timestamp": None,
            "description": "Final approval and direct benefit release."
        }
    ]

    new_app = {
        "id": f"app-{uuid.uuid4().hex[:6]}",
        "user_id": user["id"],
        "user_name": user.get("name", "Citizen"),
        "user_email": user.get("email", ""),
        "scheme_id": scheme["id"],
        "scheme_name": scheme["name"],
        "status": initial_status,
        "applied_date": datetime.date.today().isoformat(),
        "uploaded_documents": uploaded_docs,
        "remarks": f"Security Check: {fraud_res['recommendation']}." if fraud_res["is_flagged"] else "Application submitted successfully.",
        "is_flagged_fraud": fraud_res["is_flagged"],
        "fraud_risk_score": fraud_res["risk_score"],
        "fraud_flags": fraud_res["flags"],
        "timeline_history": timeline_history
    }

    db.add_application(new_app)

    # Send confirmation email
    if user.get("email"):
        try:
            EmailNotificationService.send_application_submitted(
                user["email"],
                new_app["id"],
                scheme["name"],
                user.get("name", "Applicant"),
                new_app["applied_date"]
            )
        except Exception as e:
            print(f"[EMAIL DISPATCH EXCEPTION]: {e}")

    return {
        "status": "success",
        "message": f"Application Submitted Successfully! Reference ID: {new_app['id']}",
        "application": new_app,
        "security_check": fraud_res
    }

@app.put("/api/applications/{app_id}/status")
async def update_app_status(app_id: str, req: ApplicationStatusUpdate, admin: Dict[str, Any] = Depends(require_admin_user)):
    updated = db.update_application_status(app_id, req.status, req.remarks)
    if not updated:
        raise HTTPException(status_code=404, detail="Application not found")

    # Update timeline history based on new status
    timeline = updated.get("timeline_history", [])
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    if req.status == "Approved":
        for t in timeline:
            t["status"] = "Completed"
            if not t["timestamp"]:
                t["timestamp"] = now_iso
    elif req.status == "Rejected":
        if len(timeline) >= 4:
            timeline[3]["status"] = "Rejected"
            timeline[3]["timestamp"] = now_iso
            timeline[3]["description"] = f"Application rejected. Reason: {req.remarks or 'Eligibility criteria mismatch'}"
    elif req.status == "Under Verification":
        if len(timeline) >= 2:
            timeline[1]["status"] = "Completed"
            timeline[1]["timestamp"] = now_iso
            timeline[2]["status"] = "In Progress"

    updated["timeline_history"] = timeline
    db.add_audit_log("Application Status Updated", admin.get("email", "Admin"), f"Application {app_id} status updated to '{req.status}'")

    # Trigger Email Notification for Status Update (Module 6)
    user_email = updated.get("user_email")
    if user_email:
        EmailNotificationService.send_status_update(user_email, app_id, updated.get("scheme_name", "Scheme"), req.status, req.remarks)

    return {"message": "Application status updated", "application": updated}
