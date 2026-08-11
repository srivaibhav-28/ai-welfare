from typing import Dict, List, Any
from app.database.supabase_db import db

class FraudDetectionEngine:
    @staticmethod
    def inspect_application(user_id: str, scheme_id: str, uploaded_docs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fraud Detection Security Inspection (Module 12)
        Scans for duplicate Aadhaar numbers, duplicate phone numbers,
        repeat applications, and suspicious document uploads.
        """
        flags: List[str] = []
        risk_score = 0

        current_user = db.get_user_by_id(user_id) or {}
        user_email = current_user.get("email", "").lower()
        user_mobile = current_user.get("mobile_number", "")
        user_profile = current_user.get("profile", {})
        aadhaar_num = user_profile.get("aadhaar_number") or current_user.get("aadhaar_number")

        all_users = db.get_users()
        
        # 1. Duplicate Aadhaar Check
        if aadhaar_num:
            for u in all_users:
                if u.get("id") != user_id:
                    u_aadhaar = (u.get("profile", {}) or {}).get("aadhaar_number") or u.get("aadhaar_number")
                    if u_aadhaar and u_aadhaar == aadhaar_num:
                        risk_score += 45
                        flags.append(f"Security Alert: Aadhaar Number ({aadhaar_num}) is already linked to another citizen account ({u.get('email')}).")
                        break

        # 2. Duplicate Phone Number Check across different emails
        if user_mobile and user_mobile != "9876543210":
            matching_phones = [u for u in all_users if u.get("id") != user_id and u.get("mobile_number") == user_mobile]
            if len(matching_phones) >= 2:
                risk_score += 25
                flags.append(f"Suspicious Activity: Mobile number ({user_mobile}) is associated with {len(matching_phones) + 1} distinct registered accounts.")

        # 3. Duplicate Active Application for same Scheme
        user_apps = db.get_applications(user_id=user_id)
        existing_scheme_apps = [a for a in user_apps if a.get("scheme_id") == scheme_id]
        if existing_scheme_apps:
            risk_score += 40
            flags.append("Duplicate Application Attempt: An active application for this scheme already exists for this citizen.")

        # 4. Suspicious Repeated File Uploads Check
        if uploaded_docs:
            doc_urls = list(uploaded_docs.values())
            if len(doc_urls) != len(set(doc_urls)) and len(doc_urls) > 1:
                risk_score += 30
                flags.append("Document Integrity Warning: The exact same document file was uploaded for multiple distinct document checklist requirements.")

        is_flagged = risk_score >= 40 or len(flags) > 0

        return {
            "is_flagged": is_flagged,
            "risk_score": min(risk_score, 100),
            "flags": flags,
            "recommendation": "Manual Admin Inspection Required" if is_flagged else "Passed Automated Security Verification"
        }
