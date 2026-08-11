import os
import requests
import datetime

BASE_URL = "http://127.0.0.1:8000"

def test_full_system():
    print("=" * 80)
    print("STARTING COMPLETE E2E SYSTEM AUDIT & REPAIR VERIFICATION")
    print("=" * 80)

    results = {}

    # 1. User Registration
    reg_email = f"e2etest_{datetime.datetime.now().strftime('%M%S')}@gmail.com"
    reg_payload = {
        "name": "E2E Audit User",
        "email": reg_email,
        "mobile_number": "9876543210",
        "password": "Password123",
        "confirm_password": "Password123",
        "role": "citizen"
    }

    r1 = requests.post(f"{BASE_URL}/api/auth/register", json=reg_payload)
    print(f"1. Registration API Response: Status {r1.status_code}")
    print(f"   Response Body: {r1.json()}")
    results["User Registration"] = r1.status_code == 200 and r1.json().get("status") == "otp_sent"

    # 2. OTP Verification & User Creation
    r2 = requests.post(f"{BASE_URL}/api/auth/verify-otp", json={"email": reg_email, "otp": "123456"})
    print(f"\n2. OTP Verification API Response: Status {r2.status_code}")
    print(f"   Response Body: {r2.json()}")
    results["OTP Verification & User Creation"] = r2.status_code == 200 and "access_token" in r2.json()
    user_token = r2.json().get("access_token")

    # 3. Normal User Login
    r3 = requests.post(f"{BASE_URL}/api/auth/login", json={"email": reg_email, "password": "Password123"})
    print(f"\n3. User Login API Response: Status {r3.status_code}")
    results["User Login"] = r3.status_code == 200 and r3.json().get("is_verified") == True

    # 4. Google Login
    r4 = requests.post(f"{BASE_URL}/api/auth/google", json={"email": "google_e2e@gmail.com", "name": "Google User", "role": "citizen"})
    print(f"\n4. Google Auth API Response: Status {r4.status_code}")
    results["Google Login"] = r4.status_code == 200 and "access_token" in r4.json()

    # 5. Admin Login (both admin@aiwelfare.gov and admin@welfare.gov)
    r5a = requests.post(f"{BASE_URL}/api/admin/login", json={"email": "admin@aiwelfare.gov", "password": "Admin@123"})
    print(f"\n5a. Admin Login (admin@aiwelfare.gov) Response: Status {r5a.status_code}")
    print(f"    Body: {r5a.json()}")

    r5b = requests.post(f"{BASE_URL}/api/admin/login", json={"email": "admin@welfare.gov", "password": "admin123"})
    print(f"5b. Admin Login (admin@welfare.gov) Response: Status {r5b.status_code}")
    print(f"    Body: {r5b.json()}")

    admin_token = r5a.json().get("access_token")
    results["Admin Login"] = (r5a.status_code == 200 and r5a.json().get("role") == "admin") and (r5b.status_code == 200 and r5b.json().get("role") == "admin")

    # 6. Admin Dashboard Retrieval
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    r6_dash = requests.get(f"{BASE_URL}/api/admin/dashboard", headers=admin_headers)
    print(f"\n6. Admin Dashboard Response: Status {r6_dash.status_code}")
    results["Admin Dashboard"] = r6_dash.status_code == 200 and "total_users" in r6_dash.json()

    # 7. Scheme Application & OTP Initiate
    user_headers = {"Authorization": f"Bearer {user_token}"}
    req_docs = {
        "Aadhaar Card": "aadhaar.jpg",
        "Land Ownership Document (Khatauni/Khasra)": "land.jpg",
        "Active Bank Passbook": "passbook.jpg",
        "Residence Certificate": "residence.jpg"
    }

    r7_init = requests.post(f"{BASE_URL}/api/applications/initiate-otp", headers=user_headers, json={
        "scheme_id": "scheme-001",
        "uploaded_documents": req_docs
    })
    print(f"\n7. Application OTP Initiate Response: Status {r7_init.status_code}")
    print(f"   Body: {r7_init.json()}")

    # 8. Verify Application OTP & Save Application
    r8_submit = requests.post(f"{BASE_URL}/api/applications/verify-submit-otp", headers=user_headers, json={
        "scheme_id": "scheme-001",
        "otp": "123456",
        "uploaded_documents": req_docs
    })
    print(f"\n8. Application Submit Response: Status {r8_submit.status_code}")
    print(f"   Body: {r8_submit.json()}")
    results["Application Submission & OTP Verification"] = r8_submit.status_code == 200 and "application" in r8_submit.json()

    # 9. Application Tracker Retrieval
    r9_apps = requests.get(f"{BASE_URL}/api/applications", headers=user_headers)
    print(f"\n9. Application Tracker Response: Status {r9_apps.status_code}, Count: {len(r9_apps.json())}")
    results["Application Tracker"] = r9_apps.status_code == 200 and len(r9_apps.json()) > 0

    print("\n" + "=" * 80)
    print("FINAL E2E REPAIR AUDIT RESULTS SUMMARY")
    print("=" * 80)
    all_passed = True
    for test_name, passed in results.items():
        status_str = "[PASSED]" if passed else "[FAILED]"
        print(f" - {test_name:<42}: {status_str}")
        if not passed:
            all_passed = False

    print("=" * 80)
    if all_passed:
        print("ALL E2E AUDIT TESTS COMPLETED SUCCESSFULLY!")
    else:
        print("SOME TESTS FAILED! CHECK LOGS ABOVE.")
    print("=" * 80)

if __name__ == "__main__":
    test_full_system()
