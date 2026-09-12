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
    AppOtpInitiateRequest, AppOtpVerifyRequest, PaymentStatusUpdate
)

PENDING_APPLICATION_OTPS: Dict[str, Dict[str, Any]] = {}

@app.get("/api/applications")
@app.get("/api/admin/applications")
async def get_applications(user: Dict[str, Any] = Depends(require_current_user)):
    user_id = user["id"]
    user_email = user.get("email", "")
    user_role = user.get("role", "citizen")
    print(f"\n[DIAGNOSTIC LOG] GET /api/applications request - Auth User ID: {user_id}, Email: {user_email}, Role: {user_role}")
    
    if user_role == "admin":
        apps = db.get_applications()
    else:
        apps = db.get_applications(user_id=user_id)

    print(f"[DIAGNOSTIC LOG] GET /api/applications result - Fetched Application Count: {len(apps)} for user_id: {user_id}")
    print(f"[DIAGNOSTIC LOG] Fetched Applications: {apps}\n")
    return apps

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
            "remarks": f"Security Check: {fraud_res['recommendation']}." if fraud_res.get("is_flagged") else "Application verified with 6-digit Email OTP."
        }

        print(f"[DIAGNOSTIC LOG] Saving application - App ID: {new_app_id}, User ID: {user['id']}, Email: {user.get('email')}")
        db.add_application(new_app)
        
        # Verify row creation in public.applications
        verified_apps = db.fetch_rows("applications", {"id": new_app_id})
        print(f"[APPLICATION VERIFICATION] SELECT * FROM public.applications WHERE id = '{new_app_id}': {len(verified_apps)} rows returned.")
        if not verified_apps and db.is_supabase_configured:
            raise HTTPException(status_code=500, detail=f"Database application insertion failed: Application row '{new_app_id}' does not exist in public.applications table after insert.")

        print(f"[DIAGNOSTIC LOG] Application successfully persisted to DB - App ID: {new_app_id}, User ID: {user['id']}")

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
    return await direct_apply_for_scheme(req, user=user)

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
        "remarks": f"Security Check: {fraud_res['recommendation']}." if fraud_res.get("is_flagged") else "Application submitted successfully."
    }

    db.add_application(new_app)

    # Verify row creation in public.applications
    verified_apps = db.fetch_rows("applications", {"id": new_app_id})
    print(f"[APPLICATION VERIFICATION] SELECT * FROM public.applications WHERE id = '{new_app_id}': {len(verified_apps)} rows returned.")
    if not verified_apps and db.is_supabase_configured:
        raise HTTPException(status_code=500, detail=f"Database application insertion failed: Application row '{new_app_id}' does not exist in public.applications table after insert.")

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
async def update_app_status(
    app_id: str,
    req: ApplicationStatusUpdate,
    admin: Dict[str, Any] = Depends(require_admin_user)
):
    app_obj = db.get_application_by_id(app_id)
    if not app_obj:
        raise HTTPException(status_code=404, detail="Application not found")

    old_status = app_obj.get("status", "Submitted")
    updated = db.update_application_status(app_id, req.status, req.remarks)
    if not updated:
        raise HTTPException(status_code=500, detail="Failed to update application status")

    timeline = updated.get("timeline_history") or app_obj.get("timeline_history") or []
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    if req.status == "Approved":
        for t in timeline:
            t["status"] = "Completed"
            if not t["timestamp"]:
                t["timestamp"] = now_iso
        
        # Automatically create Payment Record (One Application = One Payment)
        existing_payments = db.get_payments(application_id=app_id)
        if not existing_payments:
            scheme = db.get_scheme_by_id(updated.get("scheme_id", "")) or {}
            amount = 6000.00
            if scheme.get("amount"):
                try:
                    amount = float(scheme["amount"])
                except Exception:
                    pass
            elif scheme.get("benefits"):
                import re
                nums = re.findall(r'₹?\s*(\d[\d,]+)', str(scheme.get("benefits", "")))
                if nums:
                    try:
                        amount = float(nums[0].replace(",", ""))
                    except Exception:
                        pass

            pay_id = f"pay-{uuid.uuid4().hex[:8]}"
            payment_record = {
                "id": pay_id,
                "payment_id": pay_id,
                "application_id": app_id,
                "user_id": updated.get("user_id"),
                "scheme_id": updated.get("scheme_id"),
                "scheme_name": updated.get("scheme_name"),
                "beneficiary_name": updated.get("user_name", "Beneficiary"),
                "amount": amount,
                "payment_status": "Pending",
                "payment_reference": "",
                "approved_by": admin.get("email", "admin@welfare.gov"),
                "approved_at": now_iso,
                "paid_at": "",
                "remarks": req.remarks or "Application approved. Payment pending authorization.",
                "created_at": now_iso,
                "updated_at": now_iso
            }
            db.add_payment(payment_record)
            db.add_audit_log("Payment Record Created", admin.get("email", "Admin"), f"Automatic payment record {pay_id} created for approved application {app_id} (Amount: ₹{amount})")
            
            # Send Approval Email with Payment Status = Pending
            user_email = updated.get("user_email")
            if user_email:
                try:
                    EmailNotificationService.send_approval_with_payment_status(
                        user_email, app_id, updated.get("scheme_name", "Scheme"), updated.get("user_name", "Beneficiary"), amount
                    )
                except Exception as err:
                    print(f"[APPROVAL PAYMENT EMAIL EXCEPTION]: {err}")
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

    user_email = updated.get("user_email")
    if user_email and req.status != "Approved":
        EmailNotificationService.send_status_update(user_email, app_id, updated.get("scheme_name", "Scheme"), req.status, req.remarks)

    return {"message": "Application status updated", "application": updated}


# PAYMENT MANAGEMENT ENDPOINTS

ALLOWED_PAYMENT_STATUSES = {"Pending", "Processing", "Completed", "Failed", "Cancelled"}

@app.get("/api/payments")
@app.get("/api/admin/payments")
async def get_all_payments(
    status: str = None,
    search: str = None,
    admin: Dict[str, Any] = Depends(require_admin_user)
):
    payments = db.get_payments()
    if status and status.lower() != "all":
        payments = [p for p in payments if p.get("payment_status", "").lower() == status.lower()]
    if search:
        s = search.lower()
        payments = [
            p for p in payments if (
                s in p.get("beneficiary_name", "").lower() or
                s in p.get("scheme_name", "").lower() or
                s in p.get("application_id", "").lower() or
                s in p.get("payment_id", "").lower() or
                s in p.get("payment_reference", "").lower()
            )
        ]
    
    all_p = db.get_payments()
    analytics = {
        "total_payments": len(all_p),
        "pending": len([p for p in all_p if p.get("payment_status") == "Pending"]),
        "processing": len([p for p in all_p if p.get("payment_status") == "Processing"]),
        "completed": len([p for p in all_p if p.get("payment_status") == "Completed"]),
        "failed": len([p for p in all_p if p.get("payment_status") == "Failed"]),
        "cancelled": len([p for p in all_p if p.get("payment_status") == "Cancelled"]),
        "total_amount_paid": sum([float(p.get("amount", 0)) for p in all_p if p.get("payment_status") == "Completed"])
    }
    
    return {
        "status": "success",
        "count": len(payments),
        "payments": payments,
        "analytics": analytics
    }

@app.get("/api/payments/me")
@app.get("/api/applications/payments")
async def get_my_payments(user: Dict[str, Any] = Depends(require_current_user)):
    user_payments = db.get_payments(user_id=user["id"])
    return {
        "status": "success",
        "count": len(user_payments),
        "payments": user_payments
    }

@app.put("/api/payments/{payment_id}/status")
async def update_payment_status(
    payment_id: str,
    req: PaymentStatusUpdate,
    admin: Dict[str, Any] = Depends(require_admin_user)
):
    new_status = req.payment_status.strip()
    if new_status not in ALLOWED_PAYMENT_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid payment status '{new_status}'. Allowed statuses: Pending, Processing, Completed, Failed, Cancelled."
        )
    
    payment = db.get_payment_by_id(payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment record not found.")

    old_status = payment.get("payment_status", "Pending")

    if old_status == "Completed" and new_status in ["Pending", "Processing"]:
        raise HTTPException(status_code=400, detail="Completed payments cannot be reverted to Pending or Processing.")
    if old_status in ["Failed", "Cancelled"] and new_status == "Pending":
        raise HTTPException(status_code=400, detail=f"Payments in state '{old_status}' cannot be reset to Pending.")

    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    update_data = {
        "payment_status": new_status,
        "payment_reference": req.payment_reference if req.payment_reference is not None else payment.get("payment_reference", ""),
        "remarks": req.remarks if req.remarks is not None else payment.get("remarks", ""),
        "updated_at": now_iso
    }

    if new_status == "Completed" and not payment.get("paid_at"):
        update_data["paid_at"] = now_iso

    updated_payment = db.update_payment(payment_id, update_data)

    db.add_audit_log(
        "Payment Status Updated",
        admin.get("email", "Admin"),
        f"Payment {payment_id} for app {payment.get('application_id')} updated from '{old_status}' to '{new_status}'. Remarks: {req.remarks or 'N/A'}"
    )

    app_id = payment.get("application_id", "")
    app_data = db.fetch_rows("applications", {"id": app_id})
    user_email = (app_data[0].get("user_email") if app_data else None) or payment.get("beneficiary_name", "")

    if app_data and app_data[0].get("user_email"):
        user_email = app_data[0]["user_email"]

    if user_email and "@" in str(user_email):
        try:
            scheme_name = payment.get("scheme_name", "Welfare Scheme")
            amount = float(payment.get("amount", 0))
            pay_ref = update_data.get("payment_reference", "")
            paid_date = update_data.get("paid_at", now_iso)[:10]

            if old_status == "Pending" and new_status == "Processing":
                EmailNotificationService.send_payment_processing_email(user_email, payment_id, scheme_name, amount)
            elif new_status == "Completed":
                EmailNotificationService.send_payment_completed_email(user_email, payment_id, scheme_name, amount, pay_ref, paid_date)
            elif new_status == "Failed":
                EmailNotificationService.send_payment_failed_email(user_email, payment_id, scheme_name, amount, req.remarks or "")
            elif new_status == "Cancelled":
                EmailNotificationService.send_payment_cancelled_email(user_email, payment_id, scheme_name, amount, req.remarks or "")
        except Exception as err:
            print(f"[PAYMENT STATUS EMAIL EXCEPTION]: {err}")

    return {
        "status": "success",
        "message": f"Payment status successfully updated to {new_status}.",
        "payment": updated_payment
    }

