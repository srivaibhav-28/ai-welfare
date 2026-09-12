import os
import sys
import uuid

sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
from fastapi.testclient import TestClient
from run import app
from app.database.supabase_db import db
from app.admin_constants import ADMIN_EMAIL, ADMIN_USER_ID, ADMIN_PASSWORD_HASH

client = TestClient(app)

def verify_single_admin_strict():
    print("=" * 80)
    print("      STRICT SINGLE SYSTEM ADMINISTRATOR ARCHITECTURE VERIFICATION     ")
    print("=" * 80)

    # 1. Database Check: SELECT COUNT(*) FROM users WHERE role='admin'
    print("\n[VERIFICATION 1] Checking Supabase users table for admin count...")
    db.ensure_single_admin()
    users = db.fetch_rows("users")
    admin_users = [u for u in users if u.get("role") == "admin"]
    print(f"   Total Admin Users in Supabase: {len(admin_users)}")
    assert len(admin_users) == 1, f"Expected exactly 1 admin user in Supabase, found {len(admin_users)}"
    
    canonical_admin = admin_users[0]
    print(f"   Admin ID    : {canonical_admin.get('id')}")
    print(f"   Admin Email : {canonical_admin.get('email')}")
    print(f"   Admin Role  : {canonical_admin.get('role')}")
    assert canonical_admin.get("id") == ADMIN_USER_ID, "Admin ID mismatch!"
    assert canonical_admin.get("email") == ADMIN_EMAIL, "Admin Email mismatch!"
    assert canonical_admin.get("role") == "admin", "Admin Role mismatch!"

    # 2. Admin Login Verification
    print("\n[VERIFICATION 2] Admin Login with Environment Credentials (POST /api/admin/login)...")
    r_admin_login = client.post("/api/admin/login", json={
        "email": ADMIN_EMAIL,
        "password": "Admin@123456"
    })
    print("   Status Code:", r_admin_login.status_code)
    assert r_admin_login.status_code == 200, "Admin login failed!"
    admin_data = r_admin_login.json()
    assert admin_data.get("user_id") == ADMIN_USER_ID
    assert admin_data.get("email") == ADMIN_EMAIL
    assert admin_data.get("role") == "admin"
    admin_token = admin_data.get("access_token")
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 3. Block Citizen Login using ADMIN_EMAIL
    print("\n[VERIFICATION 3] Blocking Citizen Login using ADMIN_EMAIL (POST /api/auth/login)...")
    r_cit_admin_login = client.post("/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": "Admin@123456"
    })
    print("   Status Code:", r_cit_admin_login.status_code)
    print("   Detail:", r_cit_admin_login.json().get("detail"))
    assert r_cit_admin_login.status_code == 403, "Citizen login with admin email was not blocked!"

    # 4. Block Admin Registration
    print("\n[VERIFICATION 4] Blocking Admin Registration (POST /api/auth/register)...")
    r_admin_reg = client.post("/api/auth/register", json={
        "name": "Fake Admin",
        "email": "secondary_admin@welfare.gov",
        "mobile_number": "9999999999",
        "password": "Password123",
        "confirm_password": "Password123",
        "role": "admin"
    })
    print("   Status Code:", r_admin_reg.status_code)
    assert r_admin_reg.status_code == 403, "Admin registration was not blocked!"

    # 5. Block Secondary Admin Endpoints (register, signup, invite, import, promote)
    print("\n[VERIFICATION 5] Blocking Secondary Admin Endpoints...")
    for path in ["/api/admin/register", "/api/admin/signup", "/api/admin/invite", "/api/admin/import", "/api/admin/promote"]:
        r_sec = client.post(path, json={"email": "secondary@welfare.gov"})
        print(f"   {path} -> Status Code: {r_sec.status_code}")
        assert r_sec.status_code == 403, f"{path} was not blocked!"

    # 6. Block Google Login as Admin
    print("\n[VERIFICATION 6] Blocking Google Login as Admin (POST /api/auth/google)...")
    r_g_admin = client.post("/api/auth/google", json={
        "name": "Google Admin Attempt",
        "email": ADMIN_EMAIL,
        "role": "admin"
    })
    print("   Status Code:", r_g_admin.status_code)
    assert r_g_admin.status_code == 403, "Google login as admin was not blocked!"

    # 7. Admin Dashboard Live Database Verification
    print("\n[VERIFICATION 7] Admin Dashboard Live Data (GET /api/admin/analytics)...")
    r_dash = client.get("/api/admin/analytics", headers=admin_headers)
    print("   Status Code:", r_dash.status_code)
    assert r_dash.status_code == 200
    dash_data = r_dash.json()
    print("   Total Users Count in Dashboard        :", dash_data.get("total_users"))
    print("   Total Schemes Count in Dashboard      :", dash_data.get("total_schemes"))
    print("   Total Applications Count in Dashboard :", dash_data.get("total_applications"))

    # 8. Citizen End-to-End Flow Verification (No Regressions)
    print("\n[VERIFICATION 8] Citizen Registration, OTP, Login & Application Flow...")
    cit_email = f"test_cit_{uuid.uuid4().hex[:6]}@welfare.gov"
    cit_pwd = "CitizenPass123"

    r_c_reg = client.post("/api/auth/register", json={
        "name": "Citizen Single Test",
        "email": cit_email,
        "mobile_number": "9876543210",
        "password": cit_pwd,
        "confirm_password": cit_pwd,
        "role": "citizen"
    })
    assert r_c_reg.status_code == 200, "Citizen registration failed!"

    r_c_otp = client.post("/api/auth/verify-otp", json={
        "email": cit_email,
        "otp": "123456"
    })
    assert r_c_otp.status_code == 200, "Citizen OTP verification failed!"
    cit_token = r_c_otp.json().get("access_token")
    cit_headers = {"Authorization": f"Bearer {cit_token}"}

    r_c_login = client.post("/api/auth/login", json={"email": cit_email, "password": cit_pwd})
    assert r_c_login.status_code == 200, "Citizen login failed!"

    # Post-Verification Final Count check
    db.ensure_single_admin()
    final_users = db.fetch_rows("users")
    final_admin_count = len([u for u in final_users if u.get("role") == "admin"])
    print(f"\n[FINAL ADMIN COUNT CHECK] SELECT COUNT(*) FROM users WHERE role='admin' -> {final_admin_count}")
    assert final_admin_count == 1, "Final admin count is not 1!"

    print("\n" + "=" * 80)
    print("[OK] VERIFICATION COMPLETE: SINGLE SYSTEM ADMINISTRATOR ARCHITECTURE ENFORCED!")
    print("=" * 80)

if __name__ == "__main__":
    verify_single_admin_strict()
