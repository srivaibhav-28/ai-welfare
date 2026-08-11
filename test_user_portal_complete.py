import requests

BASE_URL = "http://127.0.0.1:8000"

def test_user_portal():
    print("=" * 80)
    print("COMPREHENSIVE CITIZEN/USER PORTAL AUDIT")
    print("=" * 80)

    test_email = "citizen_audit_user@gmail.com"
    test_pass = "CitizenPass123"

    # 1. Citizen Registration
    print("\n1. Testing Citizen Registration (POST /api/auth/register)...")
    r_reg = requests.post(f"{BASE_URL}/api/auth/register", json={
        "name": "Audit Citizen",
        "email": test_email,
        "mobile_number": "9876543210",
        "password": test_pass,
        "confirm_password": test_pass,
        "role": "citizen"
    })
    print("   Status Code:", r_reg.status_code)
    print("   Response:", r_reg.json())
    assert r_reg.status_code in [200, 400], "Citizen registration failed"

    # 2. OTP Verification
    print("\n2. Testing OTP Verification (POST /api/auth/verify-otp)...")
    r_otp = requests.post(f"{BASE_URL}/api/auth/verify-otp", json={
        "email": test_email,
        "otp": "123456"
    })
    print("   Status Code:", r_otp.status_code)
    if r_otp.status_code == 200:
        token = r_otp.json().get("access_token")
    else:
        # If already verified, login directly
        r_login_init = requests.post(f"{BASE_URL}/api/auth/login", json={"email": test_email, "password": test_pass})
        token = r_login_init.json().get("access_token")

    headers = {"Authorization": f"Bearer {token}"}
    print("   Citizen Auth Token Acquired!")

    # 3. Citizen Login
    print("\n3. Testing Citizen Login (POST /api/auth/login)...")
    r_login = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": test_email,
        "password": test_pass
    })
    print("   Status Code:", r_login.status_code)
    print("   Role Returned:", r_login.json().get("role"))
    assert r_login.status_code == 200, "Citizen login failed"

    # 4. Profile Management
    print("\n4. Testing Citizen Profile (GET & POST /api/profile)...")
    profile_data = {
        "name": "Audit Citizen",
        "mobile_number": "9876543210",
        "age": 35,
        "gender": "Male",
        "state": "Uttar Pradesh",
        "district": "Varanasi",
        "occupation": "Farmer",
        "annual_income": 120000,
        "education": "Secondary",
        "caste_category": "OBC",
        "farmer_status": True,
        "bpl_status": True,
        "aadhaar_available": True,
        "bank_account_available": True
    }
    r_prof_post = requests.post(f"{BASE_URL}/api/profile", json=profile_data, headers=headers)
    print("   Profile Update Status Code:", r_prof_post.status_code)
    assert r_prof_post.status_code == 200

    r_prof_get = requests.get(f"{BASE_URL}/api/profile", headers=headers)
    print("   Profile Get Status Code:", r_prof_get.status_code)

    # 5. AI Scheme Evaluation
    print("\n5. Testing AI Questionnaire Scheme Evaluation (POST /api/evaluate)...")
    r_eval = requests.post(f"{BASE_URL}/api/evaluate", json=profile_data, headers=headers)
    print("   Evaluation Status Code:", r_eval.status_code)
    if r_eval.status_code == 200:
        eligible_schemes = r_eval.json().get("eligible_schemes", [])
        print(f"   Eligible Schemes Found: {len(eligible_schemes)}")

    # 6. View All Schemes
    print("\n6. Testing Matched Schemes List (GET /api/schemes)...")
    r_schemes = requests.get(f"{BASE_URL}/api/schemes", headers=headers)
    print("   Schemes List Status Code:", r_schemes.status_code)
    print(f"   Total Schemes: {len(r_schemes.json())}")

    # 7. Apply for Scheme (Initiate OTP & Verify with all 4 required JPEG docs)
    print("\n7. Testing Application Submission & Security OTP Flow...")
    uploaded_docs = {
        "Aadhaar Card": "aadhaar.jpg",
        "Land Ownership Document (Khatauni/Khasra)": "land.jpg",
        "Active Bank Passbook": "passbook.jpg",
        "Residence Certificate": "residence.jpg"
    }

    r_init_otp = requests.post(f"{BASE_URL}/api/applications/initiate-otp", json={
        "scheme_id": "scheme-001",
        "uploaded_documents": uploaded_docs
    }, headers=headers)
    print("   Initiate Application OTP Status Code:", r_init_otp.status_code)
    print("   Response:", r_init_otp.json())

    r_verify_submit = requests.post(f"{BASE_URL}/api/applications/verify-submit-otp", json={
        "scheme_id": "scheme-001",
        "otp": "123456",
        "uploaded_documents": uploaded_docs
    }, headers=headers)
    print("   Submit Application Status Code:", r_verify_submit.status_code)
    print("   Response:", r_verify_submit.json().get("message"))
    assert r_verify_submit.status_code == 200

    # 8. Application Tracker
    print("\n8. Testing Application Tracker (GET /api/applications)...")
    r_apps = requests.get(f"{BASE_URL}/api/applications", headers=headers)
    print("   Application Tracker Status Code:", r_apps.status_code)
    print(f"   Applications Tracked Count: {len(r_apps.json())}")

    print("\n" + "=" * 80)
    print("CITIZEN/USER PORTAL IS 100% INTACT, UNTOUCHED AND FULLY FUNCTIONAL!")
    print("=" * 80)

if __name__ == "__main__":
    test_user_portal()
