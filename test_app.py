import requests
import json
import os
import io
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000"

def test_full_flow():
    print("--- 1. Testing Registration ---")
    reg_payload = {
        "name": "Ananya Sharma",
        "email": "ananya.sharma@example.com",
        "mobile_number": "9876543210",
        "password": "Password123",
        "role": "citizen"
    }
    
    # Register user
    from app.database import db
    # Clean up test user and reset scheme rules if modified by previous runs
    for u in list(db.data.get("users", [])):
        if u.get("email", "").lower() == reg_payload["email"].lower():
            db.delete_user(u["id"])
    for s in db.data.get("schemes", []):
        if "Widow" in s.get("name", ""):
            s["required_documents"] = ["Aadhaar Card", "Death Certificate of Husband", "Income Certificate", "Residence Certificate"]
            db.save_data()

    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)

    res = client.post("/api/auth/register", json=reg_payload)
    assert res.status_code == 200, f"Registration failed: {res.text}"
    reg_data = res.json()
    print("Registration response:", reg_data["email"], reg_data["mobile_number"])

    print("--- 2. Testing Login ---")
    login_payload = {
        "email": "ananya.sharma@example.com",
        "password": "Password123"
    }
    res = client.post("/api/auth/login", json=login_payload)
    assert res.status_code == 200, f"Login failed: {res.text}"
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("Logged in successfully! Token received.")

    print("--- 3. Testing Profile Update & Questionnaire ---")
    profile_payload = {
        "name": "Ananya Sharma",
        "mobile_number": "9876543210",
        "age": 45,
        "gender": "Female",
        "marital_status": "Widow",
        "state": "Uttar Pradesh",
        "district": "Varanasi",
        "rural_urban": "Rural",
        "education": "Secondary",
        "occupation": "Unemployed",
        "annual_income": 80000,
        "caste_category": "OBC",
        "farmer_status": False,
        "student_status": False,
        "disability_status": False,
        "senior_citizen_status": False,
        "widow_status": True,
        "bpl_status": True,
        "aadhaar_available": True,
        "bank_account_available": True
    }
    res = client.post("/api/profile", json=profile_payload, headers=headers)
    assert res.status_code == 200, f"Profile update failed: {res.text}"

    print("--- 4. Testing AI Eligibility Engine Filtering ---")
    res = client.post("/api/evaluate", json=profile_payload)
    assert res.status_code == 200
    eval_res = res.json()
    eligible_schemes = [s for s in eval_res["recommendations"] if s["is_eligible"]]
    ineligible_schemes = [s for s in eval_res["recommendations"] if not s["is_eligible"]]
    print(f"Total Schemes: {eval_res['total_schemes_analyzed']}, Eligible: {len(eligible_schemes)}, Ineligible: {len(ineligible_schemes)}")
    assert len(eligible_schemes) > 0, "Expected at least one eligible scheme (e.g. IGNWPS Widow Pension)"

    # Verify widow pension scheme is in eligible list
    widow_scheme = next((s for s in eligible_schemes if "Widow" in s["scheme_name"]), None)
    assert widow_scheme is not None, "Expected Widow Pension scheme to be eligible for female widow profile!"
    print(f"Widow Scheme matched: {widow_scheme['scheme_name']} ({widow_scheme['match_score']}%)")

    print("--- 5. Testing Document Upload Restrictions (.jpg / .jpeg only) ---")
    # Test uploading PNG (should fail)
    png_file = ("test_document.png", io.BytesIO(b"\x89PNG\r\n\x1a\nfake_image_bytes"), "image/png")
    res = client.post("/api/upload", files={"file": png_file}, data={"document_name": "Aadhaar Card"}, headers=headers)
    assert res.status_code == 400, "PNG file should be rejected!"
    print("PNG rejection verified:", res.json()["detail"])

    # Test uploading JPEG (should succeed)
    jpeg_file = ("aadhaar.jpg", io.BytesIO(b"\xff\xd8\xff\xe0fake_jpeg_header_bytes"), "image/jpeg")
    res = client.post("/api/upload", files={"file": jpeg_file}, data={"document_name": "Aadhaar Card"}, headers=headers)
    assert res.status_code == 200, f"JPEG upload failed: {res.text}"
    aadhaar_url = res.json()["file_url"]
    print("JPEG upload verified successfully! URL:", aadhaar_url)

    # Upload all required documents for widow scheme
    target_scheme_id = widow_scheme["scheme_id"]
    req_docs = widow_scheme["required_documents"]
    uploaded_docs = {}
    for doc in req_docs:
        file_tuple = (f"{doc.lower().replace(' ', '_')}.jpeg", io.BytesIO(b"\xff\xd8\xff\xe0test_jpeg"), "image/jpeg")
        up_res = client.post("/api/upload", files={"file": file_tuple}, data={"document_name": doc}, headers=headers)
        assert up_res.status_code == 200
        uploaded_docs[doc] = up_res.json()["file_url"]

    print("--- 6. Testing Application Submission ---")
    app_payload = {
        "scheme_id": target_scheme_id,
        "uploaded_documents": uploaded_docs
    }
    res = client.post("/api/applications/apply", json=app_payload, headers=headers)
    assert res.status_code == 200, f"Apply failed: {res.text}"
    msg = res.json()["message"]
    print("Application submission message:", msg)
    assert "Successfully Applied" in msg

    print("--- 7. Testing My Applications Tracker ---")
    res = client.get("/api/applications", headers=headers)
    assert res.status_code == 200
    my_apps = res.json()
    assert len(my_apps) == 1
    assert my_apps[0]["scheme_id"] == target_scheme_id
    assert my_apps[0]["status"] == "Applied"
    print("My Applications verified! App ID:", my_apps[0]["id"])

    print("--- 8. Testing Change Password ---")
    change_pass_payload = {
        "old_password": "Password123",
        "new_password": "NewSecurePassword456"
    }
    res = client.post("/api/auth/change-password", json=change_pass_payload, headers=headers)
    assert res.status_code == 200, f"Change password failed: {res.text}"
    print("Change password verified:", res.json()["message"])

    print("--- 9. Testing Admin Portal 10-Screen Endpoints ---")
    # Admin login
    admin_login_res = client.post("/api/auth/login", json={"email": "admin@welfare.gov", "password": "admin123"})
    assert admin_login_res.status_code == 200, f"Admin login failed: {admin_login_res.text}"
    admin_token = admin_login_res.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # Analytics
    analytics_res = client.get("/api/admin/analytics", headers=admin_headers)
    assert analytics_res.status_code == 200
    print("Admin Analytics verified:", analytics_res.json()["total_users"], "users,", analytics_res.json()["total_schemes"], "schemes")

    # Users list & block toggle
    users_res = client.get("/api/admin/users", headers=admin_headers)
    assert users_res.status_code == 200
    citizen_user = next((u for u in users_res.json() if u["email"] == "ananya.sharma@example.com"), None)
    assert citizen_user is not None

    block_res = client.put(f"/api/admin/users/{citizen_user['id']}/status", json={"is_blocked": True}, headers=admin_headers)
    assert block_res.status_code == 200
    unblock_res = client.put(f"/api/admin/users/{citizen_user['id']}/status", json={"is_blocked": False}, headers=admin_headers)
    assert unblock_res.status_code == 200

    # Rule Engine update
    rule_res = client.put(f"/api/admin/schemes/{target_scheme_id}/rules", json={
        "criteria": {"min_age": 18, "max_age": 60, "max_income": 200000, "widow_status": True},
        "required_documents": ["Aadhaar Card", "Income Certificate"]
    }, headers=admin_headers)
    assert rule_res.status_code == 200
    print("Rule Engine update verified:", rule_res.json()["message"])

    # Document verification desk
    doc_res = client.post("/api/admin/documents/verify", json={
        "user_id": citizen_user["id"],
        "document_name": "Aadhaar Card",
        "status": "Verified",
        "remarks": "Aadhaar card details matched successfully"
    }, headers=admin_headers)
    assert doc_res.status_code == 200
    print("Document verification desk verified:", doc_res.json()["message"])

    # Notifications broadcast
    notif_res = client.post("/api/admin/notifications", json={
        "title": "Scholarship Application Open",
        "message": "New NSP Post-Matric Scholarship is open for registration.",
        "type": "info"
    }, headers=admin_headers)
    assert notif_res.status_code == 200

    # Reports CSV export
    report_res = client.get("/api/admin/reports/export", headers=admin_headers)
    assert report_res.status_code == 200
    assert "Application ID" in report_res.text
    print("CSV Report download verified!")

    # Supabase status test
    supa_res = client.get("/api/admin/supabase-status", headers=admin_headers)
    assert supa_res.status_code == 200
    print("Supabase connection status verified:", supa_res.json()["connected"])

    print("\n[SUCCESS] ALL 10 ADMIN SCREENS AND FULL END-TO-END TESTS PASSED SUCCESSFULLY!")

def test_dashboard_uses_reusable_text_helper():
    app_js_path = Path(__file__).resolve().parent / "static" / "js" / "app.js"
    content = app_js_path.read_text(encoding="utf-8")

    assert "function setElementText(id, txt)" in content
    assert 'setElementText("dashTotalUsers"' in content


if __name__ == "__main__":
    test_full_flow()

