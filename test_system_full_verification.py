import requests
import uuid

BASE_URL = "http://127.0.0.1:8000"

def run_comprehensive_audit():
    print("=" * 80)
    print("          AI WELFARE SYSTEM COMPREHENSIVE END-TO-END VERIFICATION       ")
    print("=" * 80)

    # 1. Admin Module Verification (MUST REMAIN UNTOUCHED & 100% WORKING)
    print("\n[TEST 1] Admin Login (POST /api/admin/login)...")
    r_admin_login = requests.post(f"{BASE_URL}/api/admin/login", json={"email": "admin@aiwelfare.gov", "password": "Admin@123"})
    print("   Status Code:", r_admin_login.status_code)
    assert r_admin_login.status_code == 200, "Admin login failed!"
    admin_token = r_admin_login.json().get("access_token")
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    print("\n[TEST 2] Admin Dashboard & Analytics (GET /api/admin/analytics)...")
    r_admin_dash = requests.get(f"{BASE_URL}/api/admin/analytics", headers=admin_headers)
    print("   Status Code:", r_admin_dash.status_code)
    assert r_admin_dash.status_code == 200, "Admin dashboard failed!"

    # 2. Password Validation Error Check
    print("\n[TEST 3] Registration Mismatched Passwords Validation (POST /api/auth/register)...")
    r_mismatch = requests.post(f"{BASE_URL}/api/auth/register", json={
        "name": "Validation Test",
        "email": "valtest@gmail.com",
        "mobile_number": "9876543210",
        "password": "Password123",
        "confirm_password": "WrongPassword321",
        "role": "citizen"
    })
    print("   Status Code:", r_mismatch.status_code)
    print("   Error Detail:", r_mismatch.json().get("detail"))
    assert r_mismatch.status_code == 400 and "Passwords do not match" in r_mismatch.json().get("detail", ""), "Password mismatch validation failed!"

    # 3. Complete User Registration & OTP Flow
    unique_email = f"user_audit_{uuid.uuid4().hex[:6]}@gmail.com"
    pwd = "UserPass123"

    print(f"\n[TEST 4] User Registration with Matching Passwords ({unique_email})...")
    r_reg = requests.post(f"{BASE_URL}/api/auth/register", json={
        "name": "Audit User",
        "email": unique_email,
        "mobile_number": "9876543210",
        "password": pwd,
        "confirm_password": pwd,
        "role": "citizen"
    })
    print("   Status Code:", r_reg.status_code)
    print("   Response:", r_reg.json())
    assert r_reg.status_code == 200 and r_reg.json().get("status") == "otp_sent", "User registration failed!"

    print("\n[TEST 5] User OTP Verification (POST /api/auth/verify-otp)...")
    r_otp = requests.post(f"{BASE_URL}/api/auth/verify-otp", json={
        "email": unique_email,
        "otp": "123456"
    })
    print("   Status Code:", r_otp.status_code)
    print("   User ID Created:", r_otp.json().get("user_id"))
    print("   Is Verified:", r_otp.json().get("is_verified"))
    assert r_otp.status_code == 200 and r_otp.json().get("is_verified") == True, "OTP verification failed!"
    user_token = r_otp.json().get("access_token")
    user_headers = {"Authorization": f"Bearer {user_token}"}

    # 4. User Login Verification
    print(f"\n[TEST 6] User Login (POST /api/auth/login)...")
    r_login = requests.post(f"{BASE_URL}/api/auth/login", json={"email": unique_email, "password": pwd})
    print("   Status Code:", r_login.status_code)
    print("   User Role:", r_login.json().get("role"))
    assert r_login.status_code == 200, "User login failed!"

    # 5. Google Auth Login Verification
    print("\n[TEST 7] Google Login (POST /api/auth/google)...")
    g_email = f"google_user_{uuid.uuid4().hex[:6]}@gmail.com"
    r_google = requests.post(f"{BASE_URL}/api/auth/google", json={
        "name": "Google User",
        "email": g_email,
        "picture": "https://lh3.googleusercontent.com/a/default-user"
    })
    print("   Status Code:", r_google.status_code)
    print("   Is Verified:", r_google.json().get("is_verified"))
    assert r_google.status_code == 200, "Google login failed!"

    # 6. User Dashboard & Previously Applied Schemes & Application Tracker
    print("\n[TEST 8] User Profile & Dashboard (GET /api/profile)...")
    r_prof = requests.get(f"{BASE_URL}/api/profile", headers=user_headers)
    print("   Status Code:", r_prof.status_code)
    assert r_prof.status_code == 200, "User profile failed!"

    print("\n[TEST 9] Submit Scheme Application (POST /api/applications/initiate-otp & verify)...")
    docs = {
        "Aadhaar Card": "aadhaar.jpg",
        "Land Ownership Document (Khatauni/Khasra)": "land.jpg",
        "Active Bank Passbook": "passbook.jpg",
        "Residence Certificate": "residence.jpg"
    }
    requests.post(f"{BASE_URL}/api/applications/initiate-otp", json={"scheme_id": "scheme-001", "uploaded_documents": docs}, headers=user_headers)
    r_app_sub = requests.post(f"{BASE_URL}/api/applications/verify-submit-otp", json={"scheme_id": "scheme-001", "otp": "123456", "uploaded_documents": docs}, headers=user_headers)
    print("   Application Submit Status Code:", r_app_sub.status_code)
    assert r_app_sub.status_code == 200, "Application submission failed!"

    print("\n[TEST 10] Application Tracker & Previously Applied Schemes (GET /api/applications)...")
    r_tracker = requests.get(f"{BASE_URL}/api/applications", headers=user_headers)
    print("   Status Code:", r_tracker.status_code)
    print("   Applied Schemes Count:", len(r_tracker.json()))
    assert r_tracker.status_code == 200 and len(r_tracker.json()) > 0, "Application tracker failed!"

    print("\n" + "=" * 80)
    print("ALL 10 END-TO-END TESTS PASSED 100%! SYSTEM IS PERFECT!")
    print("=" * 80)

if __name__ == "__main__":
    run_comprehensive_audit()
