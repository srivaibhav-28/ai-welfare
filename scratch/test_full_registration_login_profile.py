import requests
import uuid
import re
import os
import time
from app.database.supabase_db import db

BASE_URL = "http://127.0.0.1:8000"
SERVER_LOG = r"C:\Users\DELL\.gemini\antigravity-ide\brain\33c57c6f-6dd5-472d-b49f-fc2c1d238bd2\.system_generated\tasks\task-1361.log"

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

def test_full_mandatory_flow():
    print("================================================================================")
    print("MANDATORY COMPLETE FLOW VERIFICATION:")
    print("Register -> Confirm Row in public.users -> Login -> Profile -> Apply -> Admin Sync")
    print("================================================================================")
    
    unique_email = f"citizen_real_{uuid.uuid4().hex[:6]}@welfare.gov"
    password = "TestPassword123"
    name = "Real Verified Citizen"
    mobile = "9876543210"
    
    # --------------------------------------------------------------------------
    # 1. REGISTER
    # --------------------------------------------------------------------------
    print(f"\n[STEP 1] Registering citizen: '{unique_email}'...")
    reg_res = requests.post(f"{BASE_URL}/api/auth/register", json={
        "name": name,
        "email": unique_email,
        "password": password,
        "mobile_number": mobile,
        "role": "citizen"
    })
    print(f"Registration response status: {reg_res.status_code}, body: {reg_res.json()}")
    assert reg_res.status_code == 200, f"Registration failed: {reg_res.text}"
    
    # Verify OTP to complete registration
    otp_code = get_otp_from_server_log(unique_email)
    print(f"Captured OTP: '{otp_code}'")
    assert otp_code is not None, "Failed to retrieve OTP from server log!"
    
    verify_res = requests.post(f"{BASE_URL}/api/auth/verify-otp", json={
        "email": unique_email,
        "otp": otp_code
    })
    print(f"OTP verification status: {verify_res.status_code}")
    assert verify_res.status_code == 200, f"OTP verification failed: {verify_res.text}"
    reg_user_id = verify_res.json()["user_id"]
    
    # --------------------------------------------------------------------------
    # 2. CONFIRM ROW EXISTS IN PUBLIC.USERS
    # --------------------------------------------------------------------------
    print(f"\n[STEP 2] Confirming row exists in public.users for '{unique_email}'...")
    db_row = db.get_user_by_email(unique_email)
    assert db_row is not None, f"FAIL: User '{unique_email}' not found in public.users table!"
    assert db_row.get("id") == reg_user_id, f"ID mismatch: db '{db_row.get('id')}' != reg '{reg_user_id}'"
    assert db_row.get("is_verified") == True, "User is_verified is False in database!"
    print(f"[PASSED] Row confirmed in public.users! ID='{db_row.get('id')}', email='{db_row.get('email')}'")
    
    # --------------------------------------------------------------------------
    # 3. LOGIN
    # --------------------------------------------------------------------------
    print(f"\n[STEP 3] Logging in citizen via POST /api/auth/login...")
    login_res = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": unique_email,
        "password": password
    })
    print(f"Login status: {login_res.status_code}")
    assert login_res.status_code == 200, f"Login failed: {login_res.text}"
    login_data = login_res.json()
    token = login_data["access_token"]
    assert login_data["user_id"] == db_row["id"], "JWT user_id mismatch with database ID!"
    print(f"[PASSED] Login successful! Reused database user ID: '{login_data['user_id']}'")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # --------------------------------------------------------------------------
    # 4. COMPLETE PROFILE
    # --------------------------------------------------------------------------
    print(f"\n[STEP 4] Completing profile via POST /api/profile...")
    profile_payload = {
        "name": name,
        "email": unique_email,
        "mobile_number": mobile,
        "aadhaar_number": "123456789012",
        "dob": "1994-06-20",
        "gender": "Male",
        "marital_status": "Single",
        "state": "Andhra Pradesh",
        "district": "Visakhapatnam",
        "mandal": "Visakhapatnam",
        "village": "Gajuwaka",
        "pincode": "530026",
        "occupation": "Farmer",
        "annual_income": 120000,
        "family_income": 180000,
        "education": "High School",
        "caste_category": "OBC",
        "disability_status": False,
        "student_status": False,
        "farmer_status": True,
        "senior_citizen_status": False,
        "widow_status": False,
        "bpl_status": True,
        "minority_status": False,
        "unemployed_status": False,
        "aadhaar_available": True,
        "bank_account_available": True,
        "bank_account_number": "98765432109876",
        "ifsc_code": "SBIN0001234",
        "rural_urban": "Rural"
    }
    prof_res = requests.post(f"{BASE_URL}/api/profile", json=profile_payload, headers=headers)
    print(f"Profile save status: {prof_res.status_code}")
    assert prof_res.status_code == 200, f"Profile save failed: {prof_res.text}"
    print(f"[PASSED] Profile saved cleanly! profile_completed={prof_res.json().get('profile_completed')}")
    
    # --------------------------------------------------------------------------
    # 5. APPLY FOR SCHEME
    # --------------------------------------------------------------------------
    print(f"\n[STEP 5] Applying for scheme via POST /api/applications/apply...")
    app_payload = {
        "scheme_id": "scheme-001",
        "scheme_name": "PM Kisan Samman Nidhi",
        "uploaded_documents": {
            "Aadhaar Card": "https://example.com/aadhaar.pdf",
            "Land Ownership Document (Khatauni/Khasra)": "https://example.com/land.pdf",
            "Active Bank Passbook": "https://example.com/passbook.pdf",
            "Residence Certificate": "https://example.com/residence.pdf"
        }
    }
    app_res = requests.post(f"{BASE_URL}/api/applications/apply", json=app_payload, headers=headers)
    print(f"Application submit status: {app_res.status_code}")
    assert app_res.status_code in [200, 201], f"Application submission failed: {app_res.text}"
    app_data = app_res.json()
    print(f"[PASSED] Application submitted! Application ID='{app_data.get('id') or app_data.get('application_id')}'")
    
    # --------------------------------------------------------------------------
    # 6. VERIFY ADMIN CAN SEE THE USER & APPLICATION
    # --------------------------------------------------------------------------
    print(f"\n[STEP 6] Verifying Admin Portal immediately sees new citizen and application...")
    admin_login_res = requests.post(f"{BASE_URL}/api/admin/login", json={"email": "admin@welfare.gov", "password": "Admin@123456"})
    admin_token = admin_login_res.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Check Admin Users endpoint
    admin_users = requests.get(f"{BASE_URL}/api/admin/users", headers=admin_headers).json()
    admin_user_row = next((u for u in admin_users if u.get("email") == unique_email), None)
    assert admin_user_row is not None, f"FAIL: Admin portal cannot see new citizen '{unique_email}'!"
    print(f"[PASSED] Admin portal sees citizen '{unique_email}'! User ID='{admin_user_row.get('id')}'")
    
    # Check Admin Applications endpoint
    admin_apps_data = admin_users_res = requests.get(f"{BASE_URL}/api/admin/applications", headers=admin_headers).json()
    admin_apps = admin_apps_data.get("applications", admin_apps_data) if isinstance(admin_apps_data, dict) else admin_apps_data
    if isinstance(admin_apps, list):
        matched_app = next((a for a in admin_apps if isinstance(a, dict) and (a.get("user_email") == unique_email or a.get("user_id") == db_row["id"])), None)
        assert matched_app is not None, f"FAIL: Admin portal cannot see application for '{unique_email}'!"
        print(f"[PASSED] Admin portal sees application ID='{matched_app.get('id')}' with status='{matched_app.get('status')}'")
    
    print("\n================================================================================")
    print("ALL MANDATORY STEPS PASSED 100% PERFECTLY!")
    print("================================================================================")

if __name__ == "__main__":
    test_full_mandatory_flow()
