import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath("."))

from dotenv import load_dotenv
load_dotenv()

from fastapi.testclient import TestClient
from run import app
from app.database.supabase_db import db
from app.admin_constants import ADMIN_EMAIL, ADMIN_USER_ID
from app.services.auth_service import create_access_token

client = TestClient(app)

def run_comprehensive_verification():
    print("=" * 80)
    print("      STRICT SINGLE SYSTEM ADMINISTRATOR COMPREHENSIVE VERIFICATION     ")
    print("=" * 80)

    # 1. Database Admin Count Check (Expected = 1)
    print("\n1. Verifying database count of users with role='admin'...")
    all_users = db.get_users()
    admin_users = [u for u in all_users if u.get("role") == "admin"]
    print(f"Total Users in DB: {len(all_users)}")
    print(f"Admin Users Count: {len(admin_users)}")
    for a in admin_users:
        print(f"   - Admin ID: {a.get('id')}, Email: {a.get('email')}, Role: {a.get('role')}")
    assert len(admin_users) == 1, f"Expected EXACTLY 1 admin user in database, found {len(admin_users)}"
    assert admin_users[0]["email"].lower() == ADMIN_EMAIL.lower(), f"Admin email mismatch: {admin_users[0]['email']} vs {ADMIN_EMAIL}"
    assert admin_users[0]["id"] == ADMIN_USER_ID, f"Admin ID mismatch: {admin_users[0]['id']} vs {ADMIN_USER_ID}"
    print("--> [PASS] Exactly ONE administrator exists in database!")

    # 2. Admin Login with Valid Env Credentials
    print("\n2. Testing Admin Login (/api/admin/login) with valid credentials...")
    login_res = client.post("/api/admin/login", json={
        "email": ADMIN_EMAIL,
        "password": "Admin@123456"
    })
    print(f"Status: {login_res.status_code}, Response: {login_res.json()}")
    assert login_res.status_code == 200, f"Expected 200, got {login_res.status_code}"
    admin_token = login_res.json()["access_token"]
    assert login_res.json()["role"] == "admin"
    assert login_res.json()["email"].lower() == ADMIN_EMAIL
    assert login_res.json()["user_id"] == ADMIN_USER_ID
    print("--> [PASS] Admin Login Successful!")

    # 3. Admin Login with Invalid Password
    print("\n3. Testing Admin Login with invalid password...")
    inv_res = client.post("/api/admin/login", json={
        "email": ADMIN_EMAIL,
        "password": "InvalidPassword123!"
    })
    print(f"Status: {inv_res.status_code}")
    assert inv_res.status_code == 401
    print("--> [PASS] Invalid password rejected with HTTP 401!")

    # 4. Admin Registration Attempts (Must return HTTP 403)
    print("\n4. Testing Admin Registration Attempt (role='admin')...")
    reg_res1 = client.post("/api/auth/register", json={
        "name": "Fake Admin",
        "email": "fake_admin@example.com",
        "mobile_number": "9999999999",
        "password": "Password@123",
        "confirm_password": "Password@123",
        "role": "admin"
    })
    print(f"Status: {reg_res1.status_code}, Detail: {reg_res1.json()}")
    assert reg_res1.status_code == 403, f"Expected 403, got {reg_res1.status_code}"

    print("Testing Registration Attempt using ADMIN_EMAIL...")
    reg_res2 = client.post("/api/auth/register", json={
        "name": "Admin Impersonator",
        "email": ADMIN_EMAIL,
        "mobile_number": "9999999999",
        "password": "Password@123",
        "confirm_password": "Password@123",
        "role": "citizen"
    })
    print(f"Status: {reg_res2.status_code}, Detail: {reg_res2.json()}")
    assert reg_res2.status_code == 403, f"Expected 403, got {reg_res2.status_code}"
    print("--> [PASS] Admin Registration Attempts blocked with HTTP 403!")

    # 5. Citizen Login using ADMIN_EMAIL (Must return HTTP 403)
    print("\n5. Testing Citizen Login (/api/auth/login) using ADMIN_EMAIL...")
    cit_admin_res = client.post("/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": "Admin@123456"
    })
    print(f"Status: {cit_admin_res.status_code}, Detail: {cit_admin_res.json()}")
    assert cit_admin_res.status_code == 403, f"Expected 403, got {cit_admin_res.status_code}"
    print("--> [PASS] Citizen login using ADMIN_EMAIL blocked with HTTP 403!")

    # 6. Admin API Authorization - Triple Verification Check
    print("\n6. Testing Admin API (/api/admin/analytics) with valid admin JWT...")
    valid_api_res = client.get("/api/admin/analytics", headers={"Authorization": f"Bearer {admin_token}"})
    print(f"Status: {valid_api_res.status_code}")
    assert valid_api_res.status_code == 200
    print("--> [PASS] Valid Admin JWT authorized!")

    print("Testing Admin API with forged token (role='admin' but wrong email)...")
    forged_token = create_access_token({"sub": "usr-hacker-01", "email": "hacker@example.com", "role": "admin", "name": "Hacker"})
    forged_res = client.get("/api/admin/analytics", headers={"Authorization": f"Bearer {forged_token}"})
    print(f"Status: {forged_res.status_code}, Detail: {forged_res.json()}")
    assert forged_res.status_code == 403, f"Expected 403, got {forged_res.status_code}"
    print("--> [PASS] Forged Admin Token rejected with HTTP 403!")

    # 7. Block Admin Creation & Promotion via DB Endpoints
    print("\n7. Testing POST /api/admin/db/users with role='admin'...")
    db_create_res = client.post("/api/admin/db/users", json={
        "id": "usr-fake-admin-99",
        "email": "newadmin@example.com",
        "role": "admin"
    }, headers={"Authorization": f"Bearer {admin_token}"})
    print(f"Status: {db_create_res.status_code}, Detail: {db_create_res.json()}")
    assert db_create_res.status_code == 403
    print("--> [PASS] DB Admin Creation blocked with HTTP 403!")

    print("Testing PUT /api/admin/db/users/{id} to promote user to role='admin'...")
    db_update_res = client.put("/api/admin/db/users/usr-citizen-01", json={
        "role": "admin"
    }, headers={"Authorization": f"Bearer {admin_token}"})
    print(f"Status: {db_update_res.status_code}, Detail: {db_update_res.json()}")
    assert db_update_res.status_code == 403
    print("--> [PASS] DB User Promotion blocked with HTTP 403!")

    # 8. Citizen System Verification (Registration & OTP & Login)
    print("\n8. Verifying Citizen Registration, Login, and Features intact...")
    cit_email = f"citizen_e2e_{os.urandom(3).hex()}@welfare.gov"
    cit_reg = client.post("/api/auth/register", json={
        "name": "E2E Citizen User",
        "email": cit_email,
        "mobile_number": "9876543210",
        "password": "Password@123",
        "confirm_password": "Password@123",
        "role": "citizen"
    })
    print(f"Citizen Register Status: {cit_reg.status_code}")
    assert cit_reg.status_code == 200

    otp_res = client.post("/api/auth/verify-otp", json={
        "email": cit_email,
        "otp": "123456"
    })
    print(f"OTP Verify Status: {otp_res.status_code}")
    assert otp_res.status_code == 200
    cit_token = otp_res.json()["access_token"]
    assert otp_res.json()["role"] == "citizen"

    # Profile get
    prof_res = client.get("/api/profile", headers={"Authorization": f"Bearer {cit_token}"})
    print(f"Profile Status: {prof_res.status_code}")
    assert prof_res.status_code == 200

    print("--> [PASS] Citizen flows working perfectly!")

    print("\n" + "=" * 80)
    print("      ALL SINGLE ADMIN VERIFICATION TESTS PASSED SUCCESSFULLY (100%)!    ")
    print("=" * 80)

if __name__ == "__main__":
    run_comprehensive_verification()
