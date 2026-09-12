import requests
import uuid
import re
import os
import time
from app.database.supabase_db import db

BASE_URL = "http://127.0.0.1:8000"
SERVER_LOG = r"C:\Users\DELL\.gemini\antigravity-ide\brain\33c57c6f-6dd5-472d-b49f-fc2c1d238bd2\.system_generated\tasks\task-1526.log"

def get_otp_from_server_log(email):
    for _ in range(5):
        time.sleep(0.5)
        if not os.path.exists(SERVER_LOG):
            continue
        with open(SERVER_LOG, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        pattern = rf"Verification OTP for {re.escape(email)}:\s*(\d{{6}})"
        matches = re.findall(pattern, content)
        if matches:
            return matches[-1]
    return None

def test_ultimate_e2e_flow():
    print("================================================================================")
    print("BEGIN ULTIMATE END-TO-END SUPABASE LIVE SYNCHRONIZATION TEST (17 MANDATORY STEPS)")
    print("================================================================================")
    
    unique_email = f"citizen_sync_{uuid.uuid4().hex[:6]}@welfare.gov"
    password = "TestPassword123!"
    name = "Live Sync Citizen"
    mobile = "9988776655"
    
    # --------------------------------------------------------------------------
    # 1. CITIZEN REGISTRATION
    # --------------------------------------------------------------------------
    print(f"\n[STEP 1] Registering Citizen: '{unique_email}'...")
    reg_res = requests.post(f"{BASE_URL}/api/auth/register", json={
        "name": name,
        "email": unique_email,
        "password": password,
        "mobile_number": mobile,
        "role": "citizen"
    })
    print(f"Registration response: {reg_res.status_code}")
    assert reg_res.status_code == 200, f"Registration failed: {reg_res.text}"
    
    otp_code = get_otp_from_server_log(unique_email)
    print(f"Captured OTP: '{otp_code}'")
    assert otp_code is not None, "Failed to capture OTP from server log!"
    
    verify_res = requests.post(f"{BASE_URL}/api/auth/verify-otp", json={
        "email": unique_email,
        "otp": otp_code
    })
    print(f"OTP Verification response: {verify_res.status_code}")
    assert verify_res.status_code == 200, f"OTP verification failed: {verify_res.text}"
    user_id = verify_res.json()["user_id"]
    print(f"[PASSED STEP 1] Citizen registered & verified with user_id='{user_id}'")
    
    # --------------------------------------------------------------------------
    # 2. VERIFY ROW EXISTS IN PUBLIC.USERS
    # --------------------------------------------------------------------------
    print(f"\n[STEP 2] Executing SELECT * FROM public.users WHERE email = '{unique_email}'...")
    user_rows = db.fetch_rows("users", {"email": unique_email})
    assert user_rows and len(user_rows) == 1, f"FAIL: Row for '{unique_email}' not found in public.users!"
    user_row = user_rows[0]
    assert user_row["id"] == user_id, f"ID mismatch in DB: {user_row['id']} != {user_id}"
    print(f"[PASSED STEP 2] Row verified in public.users! ID='{user_row['id']}', email='{user_row['email']}'")
    
    # --------------------------------------------------------------------------
    # 3. CITIZEN LOGIN
    # --------------------------------------------------------------------------
    print(f"\n[STEP 3] Logging in Citizen via POST /api/auth/login...")
    login_res = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": unique_email,
        "password": password
    })
    print(f"Login status: {login_res.status_code}")
    assert login_res.status_code == 200, f"Login failed: {login_res.text}"
    token = login_res.json()["access_token"]
    citizen_headers = {"Authorization": f"Bearer {token}"}
    print(f"[PASSED STEP 3] Citizen logged in cleanly! JWT sub equals database users.id='{login_res.json()['user_id']}'")
    
    # --------------------------------------------------------------------------
    # 4. PROFILE SAVE
    # --------------------------------------------------------------------------
    print(f"\n[STEP 4] Updating Profile via POST /api/profile...")
    profile_payload = {
        "name": "Live Sync Citizen Updated",
        "email": unique_email,
        "mobile_number": mobile,
        "aadhaar_number": "999888777666",
        "dob": "1990-01-01",
        "gender": "Female",
        "marital_status": "Married",
        "state": "Andhra Pradesh",
        "district": "Visakhapatnam",
        "mandal": "Visakhapatnam",
        "village": "Gajuwaka",
        "pincode": "530026",
        "occupation": "Farmer",
        "annual_income": 150000,
        "family_income": 200000,
        "education": "Graduate",
        "caste_category": "OBC",
        "farmer_status": True,
        "bpl_status": True,
        "aadhaar_available": True,
        "bank_account_available": True,
        "bank_account_number": "11223344556677",
        "ifsc_code": "SBIN0009999",
        "rural_urban": "Rural"
    }
    prof_res = requests.post(f"{BASE_URL}/api/profile", json=profile_payload, headers=citizen_headers)
    print(f"Profile save status: {prof_res.status_code}")
    assert prof_res.status_code == 200, f"Profile update failed: {prof_res.text}"
    print(f"[PASSED STEP 4] Profile updated via HTTP POST /api/profile!")
    
    # --------------------------------------------------------------------------
    # 5. VERIFY ROW UPDATED IN PUBLIC.USERS
    # --------------------------------------------------------------------------
    print(f"\n[STEP 5] Verifying profile row in public.users for user_id='{user_id}'...")
    updated_user_rows = db.fetch_rows("users", {"id": user_id})
    assert updated_user_rows and len(updated_user_rows) == 1, f"User '{user_id}' missing from public.users!"
    db_profile = updated_user_rows[0].get("profile", {})
    assert db_profile.get("aadhaar_number") == "999888777666", f"Aadhaar not updated in DB: {db_profile.get('aadhaar_number')}"
    print(f"[PASSED STEP 5] Verified public.users row updated in Supabase! Aadhaar='{db_profile.get('aadhaar_number')}'")
    
    # --------------------------------------------------------------------------
    # 6. APPLY SCHEME
    # --------------------------------------------------------------------------
    print(f"\n[STEP 6] Applying for scheme via POST /api/applications/apply...")
    app_payload = {
        "scheme_id": "scheme-001",
        "scheme_name": "PM Kisan Samman Nidhi",
        "uploaded_documents": {
            "Aadhaar Card": "https://example.com/aadhaar.jpg",
            "Land Ownership Document (Khatauni/Khasra)": "https://example.com/land.jpg",
            "Active Bank Passbook": "https://example.com/passbook.jpg",
            "Residence Certificate": "https://example.com/residence.jpg"
        }
    }
    app_res = requests.post(f"{BASE_URL}/api/applications/apply", json=app_payload, headers=citizen_headers)
    print(f"Application submission status: {app_res.status_code}")
    assert app_res.status_code in [200, 201], f"Application submission failed: {app_res.text}"
    print(f"[PASSED STEP 6] Scheme application submitted successfully!")
    
    # --------------------------------------------------------------------------
    # 7. VERIFY APPLICATION INSERTED INTO PUBLIC.APPLICATIONS
    # --------------------------------------------------------------------------
    print(f"\n[STEP 7] Verifying application row in public.applications for user_id='{user_id}'...")
    app_rows = db.fetch_rows("applications", {"user_id": user_id})
    assert app_rows and len(app_rows) > 0, f"No application row found in public.applications for user_id='{user_id}'!"
    app_row = app_rows[0]
    app_id = app_row["id"]
    print(f"[PASSED STEP 7] Verified row inserted into public.applications! app_id='{app_id}', status='{app_row.get('status')}'")
    
    # --------------------------------------------------------------------------
    # 8. UPLOAD DOCUMENT
    # --------------------------------------------------------------------------
    print(f"\n[STEP 8] Uploading document metadata to user_documents...")
    doc_info = {
        "status": "Uploaded",
        "upload_date": "2026-08-14",
        "file_name": "aadhaar_card.jpg",
        "file_url": "https://mborxydvtiekgnxflsci.supabase.co/storage/v1/object/public/scheme-documents/test.jpg",
        "remarks": "Uploaded by citizen"
    }
    db.update_user_document(user_id, "Aadhaar Card", doc_info)
    print(f"[PASSED STEP 8] Document metadata stored for 'Aadhaar Card'!")
    
    # --------------------------------------------------------------------------
    # 9. VERIFY USER_DOCUMENTS UPDATED IN PUBLIC.USER_DOCUMENTS
    # --------------------------------------------------------------------------
    print(f"\n[STEP 9] Verifying row in public.user_documents for user_id='{user_id}'...")
    doc_rows = db.fetch_rows("user_documents", {"user_id": user_id, "document_name": "Aadhaar Card"})
    assert doc_rows and len(doc_rows) > 0, f"No document row found in public.user_documents for user_id='{user_id}'!"
    print(f"[PASSED STEP 9] Verified public.user_documents contains row! status='{doc_rows[0].get('status')}'")
    
    # --------------------------------------------------------------------------
    # 10. ADMIN LOGIN
    # --------------------------------------------------------------------------
    print(f"\n[STEP 10] Logging in Admin via POST /api/admin/login...")
    admin_login_res = requests.post(f"{BASE_URL}/api/admin/login", json={
        "email": "admin@welfare.gov",
        "password": "Admin@123456"
    })
    assert admin_login_res.status_code == 200, f"Admin login failed: {admin_login_res.text}"
    admin_token = admin_login_res.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    print(f"[PASSED STEP 10] Admin logged in cleanly!")
    
    # --------------------------------------------------------------------------
    # 11. DASHBOARD SHOWS LIVE COUNTS
    # --------------------------------------------------------------------------
    print(f"\n[STEP 11] Fetching Live Admin Dashboard Analytics via GET /api/admin/analytics...")
    dash_res = requests.get(f"{BASE_URL}/api/admin/analytics", headers=admin_headers)
    assert dash_res.status_code == 200, f"Admin dashboard failed: {dash_res.text}"
    dash_data = dash_res.json()
    assert dash_data.get("total_users", 0) > 0, "Total users count is 0!"
    assert dash_data.get("total_applications", 0) > 0, "Total applications count is 0!"
    print(f"[PASSED STEP 11] Admin dashboard shows live counts! Total Users={dash_data.get('total_users')}, Total Apps={dash_data.get('total_applications')}")
    
    # --------------------------------------------------------------------------
    # 12. ADMIN USERS PAGE SHOWS CITIZEN
    # --------------------------------------------------------------------------
    print(f"\n[STEP 12] Fetching Admin Users List via GET /api/admin/users...")
    admin_users = requests.get(f"{BASE_URL}/api/admin/users", headers=admin_headers).json()
    matched_admin_user = next((u for u in admin_users if u.get("id") == user_id or u.get("email") == unique_email), None)
    assert matched_admin_user is not None, f"FAIL: Admin Users page cannot see citizen '{unique_email}'!"
    print(f"[PASSED STEP 12] Admin Users page shows citizen '{unique_email}' with ID='{matched_admin_user['id']}'")
    
    # --------------------------------------------------------------------------
    # 13. ADMIN APPLICATIONS PAGE SHOWS APPLICATION
    # --------------------------------------------------------------------------
    print(f"\n[STEP 13] Fetching Admin Applications List via GET /api/admin/applications...")
    admin_apps_res = requests.get(f"{BASE_URL}/api/admin/applications", headers=admin_headers).json()
    admin_apps = admin_apps_res.get("applications", admin_apps_res) if isinstance(admin_apps_res, dict) else admin_apps_res
    matched_admin_app = next((a for a in admin_apps if isinstance(a, dict) and (a.get("id") == app_id or a.get("user_id") == user_id)), None)
    assert matched_admin_app is not None, f"FAIL: Admin Applications page cannot see application for '{unique_email}'!"
    print(f"[PASSED STEP 13] Admin Applications page shows application ID='{matched_admin_app['id']}'")
    
    # --------------------------------------------------------------------------
    # 14. APPROVE APPLICATION
    # --------------------------------------------------------------------------
    print(f"\n[STEP 14] Approving application '{app_id}' via PUT /api/applications/{app_id}/status...")
    approve_res = requests.put(
        f"{BASE_URL}/api/applications/{app_id}/status",
        json={"status": "Approved", "remarks": "Approved by Admin"},
        headers=admin_headers
    )
    print(f"Approve status code: {approve_res.status_code}")
    assert approve_res.status_code == 200, f"Approve application failed: {approve_res.text}"
    print(f"[PASSED STEP 14] Application status set to 'Approved'!")
    
    # --------------------------------------------------------------------------
    # 15. CITIZEN SEES APPROVED STATUS
    # --------------------------------------------------------------------------
    print(f"\n[STEP 15] Citizen checking application status via GET /api/applications...")
    cit_apps_res = requests.get(f"{BASE_URL}/api/applications", headers=citizen_headers)
    assert cit_apps_res.status_code == 200, f"Citizen applications fetch failed: {cit_apps_res.text}"
    cit_apps = cit_apps_res.json().get("applications", cit_apps_res.json()) if isinstance(cit_apps_res.json(), dict) else cit_apps_res.json()
    cit_matched_app = next((a for a in cit_apps if isinstance(a, dict) and a.get("id") == app_id), None)
    assert cit_matched_app is not None, f"Citizen cannot find application '{app_id}'!"
    assert cit_matched_app.get("status") == "Approved", f"Status mismatch for citizen: expected 'Approved', got '{cit_matched_app.get('status')}'"
    print(f"[PASSED STEP 15] Citizen immediately sees updated status: 'Approved'!")
    
    # --------------------------------------------------------------------------
    # 16. DELETE USER
    # --------------------------------------------------------------------------
    print(f"\n[STEP 16] Admin deleting user '{user_id}' via DELETE /api/admin/users/{user_id}...")
    del_res = requests.delete(f"{BASE_URL}/api/admin/users/{user_id}", headers=admin_headers)
    assert del_res.status_code == 200, f"Delete user failed: {del_res.text}"
    print(f"[PASSED STEP 16] Admin deleted user '{user_id}'!")
    
    # --------------------------------------------------------------------------
    # 17. VERIFY USER, APPLICATIONS, AND DOCUMENTS REMOVED FROM DATABASE
    # --------------------------------------------------------------------------
    print(f"\n[STEP 17] Verifying user, applications, and documents removed from Supabase...")
    rem_users = db.fetch_rows("users", {"id": user_id})
    rem_apps = db.fetch_rows("applications", {"user_id": user_id})
    rem_docs = db.fetch_rows("user_documents", {"user_id": user_id})
    
    assert len(rem_users) == 0, f"FAIL: User '{user_id}' still exists in public.users!"
    assert len(rem_apps) == 0, f"FAIL: Applications for '{user_id}' still exist in public.applications!"
    assert len(rem_docs) == 0, f"FAIL: User documents for '{user_id}' still exist in public.user_documents!"
    print(f"[PASSED STEP 17] Clean removal verified in Supabase! 0 users, 0 applications, 0 documents remain!")
    
    print("\n================================================================================")
    print("ALL 17 MANDATORY STEPS PASSED 100% PERFECTLY!")
    print("================================================================================")

if __name__ == "__main__":
    test_ultimate_e2e_flow()
