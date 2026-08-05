import io
from fastapi.testclient import TestClient

from api.auth import app as auth_app
from api.users import app as users_app
from api.schemes import app as schemes_app
from api.eligibility import app as eligibility_app
from api.applications import app as applications_app
from api.documents import app as documents_app
from api.admin import app as admin_app
from api.reports import app as reports_app
from app.database.supabase_db import db

def test_full_verifications():
    print("--- 1. Testing Registration ---")
    auth_client = TestClient(auth_app)
    users_client = TestClient(users_app)
    schemes_client = TestClient(schemes_app)
    eligibility_client = TestClient(eligibility_app)
    applications_client = TestClient(applications_app)
    documents_client = TestClient(documents_app)
    admin_client = TestClient(admin_app)
    reports_client = TestClient(reports_app)

    reg_payload = {
        "name": "Ananya Sharma",
        "email": "test.ananya.sharma@example.com",
        "mobile_number": "9876543210",
        "password": "Password123",
        "role": "citizen"
    }
    
    # Reset existing user if present
    db.delete_user("usr-test-ananya")
    existing = db.get_user_by_email("test.ananya.sharma@example.com")
    if existing:
        db.delete_user(existing["id"])

    res = auth_client.post("/api/auth/register", json=reg_payload)
    assert res.status_code == 200, f"Registration failed: {res.text}"
    reg_data = res.json()
    token = reg_data["access_token"]
    user_id = reg_data["user_id"]
    headers = {"Authorization": f"Bearer {token}"}
    print("Registered successfully:", reg_data["email"], reg_data["mobile_number"])

    print("--- 2. Testing Login ---")
    login_payload = {
        "email": "test.ananya.sharma@example.com",
        "password": "Password123"
    }
    res = auth_client.post("/api/auth/login", json=login_payload)
    assert res.status_code == 200, f"Login failed: {res.text}"
    print("Logged in successfully!")

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
        "occupation": "Self-Employed",
        "annual_income": 80000,
        "education": "Secondary",
        "caste_category": "General",
        "disability_status": False,
        "student_status": False,
        "farmer_status": False,
        "senior_citizen_status": False,
        "widow_status": True,
        "bpl_status": True,
        "aadhaar_available": True,
        "bank_account_available": True
    }
    res = users_client.post("/api/profile", json=profile_payload, headers=headers)
    assert res.status_code == 200, f"Profile update failed: {res.text}"
    print("Profile updated successfully!")

    print("--- 4. Testing AI Recommendation Engine ---")
    res = eligibility_client.post("/api/evaluate", json=profile_payload)
    assert res.status_code == 200, f"Evaluation failed: {res.text}"
    eval_data = res.json()
    print(f"Engine evaluated {eval_data['total_schemes_analyzed']} schemes. Eligible: {eval_data['eligible_schemes_count']}")
    assert eval_data["eligible_schemes_count"] > 0, "Citizen should qualify for eligible schemes!"

    print("--- 5. Testing Schemes API ---")
    res = schemes_client.get("/api/schemes")
    assert res.status_code == 200, "Schemes list failed"
    schemes = res.json()
    print(f"Total schemes fetched: {len(schemes)}")

    print("--- 6. Testing Document Upload (Strict JPEG Validation) ---")
    dummy_jpeg_bytes = b"\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xFF\xDB\x00C\x00" + b"\x00" * 50
    files = {"file": ("aadhaar.jpg", dummy_jpeg_bytes, "image/jpeg")}
    data = {"document_name": "Aadhaar Card"}
    res = documents_client.post("/api/upload", files=files, data=data, headers=headers)
    assert res.status_code == 200, f"JPEG Document upload failed: {res.text}"
    upload_res = res.json()
    print("Uploaded document URL:", upload_res["file_url"])

    print("--- 7. Testing Document Checklist ---")
    res = documents_client.get("/api/documents", headers=headers)
    assert res.status_code == 200, f"Get documents failed: {res.text}"
    checklist = res.json()
    print("Smart Checklist items:", len(checklist))

    print("--- 8. Testing Apply for Scheme ---")
    target_scheme = schemes[0]
    req_docs = target_scheme.get("required_documents", [])
    uploaded_map = {d: upload_res["file_url"] for d in req_docs}
    app_payload = {
        "scheme_id": target_scheme["id"],
        "uploaded_documents": uploaded_map
    }
    res = applications_client.post("/api/applications/apply", json=app_payload, headers=headers)
    assert res.status_code == 200, f"Apply for scheme failed: {res.text}"
    app_res = res.json()
    print("Applied successfully! Application ID:", app_res["application"]["id"])

    print("--- 9. Testing Application Tracker ---")
    res = applications_client.get("/api/applications", headers=headers)
    assert res.status_code == 200, "Fetch applications failed"
    user_apps = res.json()
    print(f"Total applications for user: {len(user_apps)}")

    print("--- 10. Testing Admin Operations ---")
    admin_login_res = auth_client.post("/api/auth/login", json={"email": "admin@welfare.gov", "password": "admin123"})
    assert admin_login_res.status_code == 200, "Admin login failed"
    admin_token = admin_login_res.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    res = admin_client.get("/api/admin/analytics", headers=admin_headers)
    assert res.status_code == 200, "Admin analytics failed"
    analytics = res.json()
    print("Admin Analytics Summary - Users:", analytics["total_users"], "Applications:", analytics["total_applications"])

    res = reports_client.get("/api/admin/reports/export", headers=admin_headers)
    assert res.status_code == 200, "Admin report export failed"
    assert "Application ID" in res.text, "Report CSV output invalid"
    print("Admin Report Export verified successfully!")

    print("\n[SUCCESS] ALL END-TO-END VERIFICATIONS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_full_verifications()
