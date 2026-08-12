import requests
import json
import uuid

BASE_URL = "http://127.0.0.1:8000"

def run_stabilization_full_regression():
    print("=" * 80)
    print("      PROJECT STABILIZATION MODE - FULL REGRESSION & REDIRECT FLOW TEST     ")
    print("=" * 80)

    test_email = f"stab_user_{uuid.uuid4().hex[:6]}@gmail.com"
    pwd = "MySecurePassword123"

    # Step 1: Register New User
    print("\n1. Testing Registration (POST /api/auth/register)...")
    r_reg = requests.post(f"{BASE_URL}/api/auth/register", json={
        "name": "Stabilization User",
        "email": test_email,
        "mobile_number": "9876543210",
        "password": pwd,
        "confirm": pwd,
        "role": "citizen"
    })
    assert r_reg.status_code == 200, f"Registration failed: {r_reg.text}"
    print("[PASS] Registration successful")

    # Step 2: Verify Registration OTP
    print("\n2. Testing OTP Verification (POST /api/auth/verify-otp)...")
    r_otp = requests.post(f"{BASE_URL}/api/auth/verify-otp", json={
        "email": test_email,
        "otp": "123456"
    })
    assert r_otp.status_code == 200, f"OTP verification failed: {r_otp.text}"
    token = r_otp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("[PASS] Registration OTP verified successfully")

    # Step 3: Login & Verify Initial Incomplete Profile Redirect Status
    print("\n3. Testing Login & Checking Profile Completion Status...")
    r_login = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": test_email,
        "password": pwd
    })
    assert r_login.status_code == 200, f"Login failed: {r_login.text}"
    
    r_prof = requests.get(f"{BASE_URL}/api/profile", headers=headers)
    assert r_prof.status_code == 200
    prof_data = r_prof.json()
    assert prof_data.get("profile_completed") is False, "Newly registered user must start with profile_completed = False!"
    assert prof_data.get("name") == "Stabilization User", "New user name must match registered name!"
    assert prof_data.get("mobile_number") == "9876543210", "New user mobile must match registered mobile!"
    assert prof_data.get("aadhaar_number", "") == "", "Aadhaar must be empty for new user!"
    assert prof_data.get("dob", "") == "", "DOB must be empty for new user!"
    assert prof_data.get("state", "") == "", "State must be empty for new user!"
    assert prof_data.get("district", "") == "", "District must be empty for new user!"
    assert prof_data.get("pincode", "") == "", "Pincode must be empty for new user!"
    assert prof_data.get("bank_account_number", "") == "", "Bank account must be empty for new user!"
    assert prof_data.get("ifsc_code", "") == "", "IFSC code must be empty for new user!"
    assert prof_data.get("annual_income", 0) == 0, "Annual income must be 0 for new user!"
    print("[PASS] Newly registered user has ONLY name/mobile prefilled and ZERO demo/fallback values")

    # Step 4: Test Incomplete Profile Submission (Validation Error Check)
    print("\n4. Testing Incomplete Profile Submission Validation...")
    r_bad_prof = requests.post(f"{BASE_URL}/api/profile", headers=headers, json={
        "name": "Stabilization User",
        "mobile_number": "9876543210",
        "aadhaar_number": "123", # Invalid length
        "dob": "",
        "district": "",
        "pincode": "221",
        "bank_account_number": ""
    })
    assert r_bad_prof.status_code == 200
    assert r_bad_prof.json().get("profile_completed") is False, "Incomplete profile must NOT be marked profile_completed = True!"
    print("[PASS] Incomplete profile correctly rejected from marking profile_completed = True")

    # Step 5: Test Full Valid Profile Completion
    print("\n5. Testing Valid Profile Save (POST /api/profile)...")
    valid_profile = {
        "name": "Stabilization User",
        "mobile_number": "9876543210",
        "aadhaar_number": "123456789012",
        "dob": "1996-06-20",
        "gender": "Male",
        "marital_status": "Single",
        "state": "Uttar Pradesh",
        "district": "Varanasi",
        "mandal": "Sadar",
        "village": "Shivpur",
        "pincode": "221001",
        "rural_urban": "Rural",
        "occupation": "Farmer",
        "annual_income": 150000,
        "family_income": 180000,
        "bank_account_number": "987654321098",
        "ifsc_code": "SBIN0001234",
        "education": "Secondary",
        "caste_category": "General",
        "farmer_status": True,
        "student_status": False,
        "disability_status": False,
        "senior_citizen_status": False,
        "widow_status": False,
        "bpl_status": True,
        "minority_status": False,
        "unemployed_status": False,
        "aadhaar_available": True,
        "bank_account_available": True,
        "profile_completed": True
    }
    r_good_prof = requests.post(f"{BASE_URL}/api/profile", headers=headers, json=valid_profile)
    assert r_good_prof.status_code == 200
    assert r_good_prof.json().get("profile_completed") is True, "Valid profile must be marked profile_completed = True!"
    print("[PASS] Valid profile completed and saved with profile_completed = TRUE")

    # Step 6: Test Eligibility Evaluation & Questionnaire Flow
    print("\n6. Testing AI Eligibility Engine Evaluation...")
    r_eval = requests.post(f"{BASE_URL}/api/evaluate", json=valid_profile)
    assert r_eval.status_code == 200
    eval_data = r_eval.json()
    assert "recommendations" in eval_data
    print(f"[PASS] AI Eligibility Engine evaluated profile ({len(eval_data['recommendations'])} schemes recommended)")

    # Step 7: Test Login for User with Completed Profile
    print("\n7. Testing Login for Citizen with Completed Profile...")
    r_login_again = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": test_email,
        "password": pwd
    })
    assert r_login_again.status_code == 200
    r_prof_again = requests.get(f"{BASE_URL}/api/profile", headers=headers)
    assert r_prof_again.json().get("profile_completed") is True
    print("[PASS] Existing user with complete profile correctly evaluates profile_completed = TRUE (Direct to Dashboard)")

    # Step 8: Test Admin Login
    print("\n8. Testing Admin Login (POST /api/auth/login)...")
    r_admin_login = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "admin@welfare.gov",
        "password": "admin123"
    })
    if r_admin_login.status_code != 200:
        r_admin_login = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@welfare.gov",
            "password": "Admin@123"
        })
    assert r_admin_login.status_code == 200
    assert r_admin_login.json()["role"] == "admin"
    print("[PASS] Admin login successful")

    # Step 9: Test Scheme Application Security OTP
    print("\n9. Testing Scheme Application & OTP Flow...")
    uploaded_docs_payload = {
        "Aadhaar Card": "aadhaar.jpg",
        "Land Ownership Document (Khatauni/Khasra)": "land.jpg",
        "Active Bank Passbook": "passbook.jpg",
        "Residence Certificate": "residence.jpg"
    }
    r_app_otp = requests.post(f"{BASE_URL}/api/applications/initiate-otp", headers=headers, json={
        "scheme_id": "scheme-001",
        "uploaded_documents": uploaded_docs_payload
    })
    assert r_app_otp.status_code == 200, f"App OTP initiation failed: {r_app_otp.text}"
    assert r_app_otp.json()["status"] == "otp_sent"

    r_app_submit = requests.post(f"{BASE_URL}/api/applications/verify-submit-otp", headers=headers, json={
        "scheme_id": "scheme-001",
        "otp": "123456",
        "uploaded_documents": uploaded_docs_payload
    })
    assert r_app_submit.status_code == 200, f"App submission failed: {r_app_submit.text}"
    assert r_app_submit.json()["status"] == "success"
    print("[PASS] Scheme application & security OTP verification successful")

    print("\n" + "=" * 80)
    print("ALL 9 STABILIZATION & REGRESSION SUITE TESTS PASSED 100%!")
    print("=" * 80)

if __name__ == "__main__":
    run_stabilization_full_regression()
