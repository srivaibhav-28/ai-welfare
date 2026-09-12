import os
import sys
import uuid

sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
from fastapi.testclient import TestClient
from run import app
from app.database.supabase_db import db
from app.admin_constants import ADMIN_EMAIL, ADMIN_USER_ID, ADMIN_PASSWORD_HASH

client = TestClient(app)

def verify_database_backed_single_admin():
    print("=" * 80)
    print("  DATABASE-BACKED SINGLE SYSTEM ADMINISTRATOR ARCHITECTURE VERIFICATION ")
    print("=" * 80)

    # 1. Supabase Database Count Check: SELECT COUNT(*) FROM users WHERE role='admin'
    print("\n[TEST 1] Verifying live Supabase users table for admin count...")
    db.ensure_single_admin()
    users = db.fetch_rows("users")
    admin_users = [u for u in users if u.get("role") == "admin"]
    print(f"   Total Admin Users in Supabase: {len(admin_users)}")
    assert len(admin_users) == 1, f"Expected exactly 1 admin user in Supabase, found {len(admin_users)}"
    
    canonical_admin = admin_users[0]
    print(f"   Admin ID            : {canonical_admin.get('id')}")
    print(f"   Admin Email         : {canonical_admin.get('email')}")
    print(f"   Admin Role          : {canonical_admin.get('role')}")
    print(f"   Admin Password Hash : {canonical_admin.get('password_hash')[:30]}...")
    assert canonical_admin.get("id") == ADMIN_USER_ID, "Admin ID mismatch!"
    assert canonical_admin.get("email") == ADMIN_EMAIL, "Admin Email mismatch!"
    assert canonical_admin.get("role") == "admin", "Admin Role mismatch!"
    assert canonical_admin.get("password_hash") is not None, "Admin password hash missing!"

    # 2. Admin Login using Existing Standard Login Page (/api/auth/login)
    print("\n[TEST 2] Admin Login via Existing Standard Login Page (POST /api/auth/login)...")
    r_admin_login = client.post("/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": "Admin@123456"
    })
    print("   Status Code:", r_admin_login.status_code)
    assert r_admin_login.status_code == 200, f"Admin login failed: {r_admin_login.text}"
    admin_data = r_admin_login.json()
    print("   Role Returned      :", admin_data.get("role"))
    print("   User ID Returned   :", admin_data.get("user_id"))
    print("   Email Returned     :", admin_data.get("email"))
    assert admin_data.get("user_id") == ADMIN_USER_ID
    assert admin_data.get("email") == ADMIN_EMAIL
    assert admin_data.get("role") == "admin"
    admin_token = admin_data.get("access_token")
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 3. Invalid Admin Password Attempt (/api/auth/login)
    print("\n[TEST 3] Invalid Admin Password Attempt (POST /api/auth/login)...")
    r_invalid_login = client.post("/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": "WrongAdminPassword123"
    })
    print("   Status Code:", r_invalid_login.status_code)
    assert r_invalid_login.status_code == 401, "Invalid admin login was not rejected!"

    # 4. Citizen Registration & Login via Existing Standard Login Page (/api/auth/login)
    print("\n[TEST 4] Citizen Registration & Login via Standard Login Page...")
    cit_email = f"test_cit_{uuid.uuid4().hex[:6]}@welfare.gov"
    cit_pwd = "CitizenPass123"

    r_c_reg = client.post("/api/auth/register", json={
        "name": "Citizen Database Test",
        "email": cit_email,
        "mobile_number": "9876543210",
        "password": cit_pwd,
        "confirm_password": cit_pwd,
        "role": "citizen"
    })
    assert r_c_reg.status_code == 200, f"Citizen registration failed: {r_c_reg.text}"

    client.post("/api/auth/verify-otp", json={
        "email": cit_email,
        "otp": "123456"
    })

    r_c_login = client.post("/api/auth/login", json={"email": cit_email, "password": cit_pwd})
    print("   Citizen Login Status Code:", r_c_login.status_code)
    print("   Citizen Role Returned     :", r_c_login.json().get("role"))
    assert r_c_login.status_code == 200, "Citizen login failed!"
    assert r_c_login.json().get("role") == "citizen", "Citizen role mismatch!"

    # 5. Block Admin Registration
    print("\n[TEST 5] Blocking Admin Registration (POST /api/auth/register)...")
    r_admin_reg = client.post("/api/auth/register", json={
        "name": "Fake Admin Attempt",
        "email": "secondary_admin@welfare.gov",
        "mobile_number": "9999999999",
        "password": "Password123",
        "confirm_password": "Password123",
        "role": "admin"
    })
    print("   Status Code:", r_admin_reg.status_code)
    assert r_admin_reg.status_code == 403, "Admin registration was not blocked!"

    # 6. Block Secondary Admin Endpoints (register, signup, invite, import, promote)
    print("\n[TEST 6] Blocking Secondary Admin Endpoints...")
    for path in ["/api/admin/register", "/api/admin/signup", "/api/admin/invite", "/api/admin/import", "/api/admin/promote"]:
        r_sec = client.post(path, json={"email": "secondary@welfare.gov"})
        print(f"   {path} -> Status Code: {r_sec.status_code}")
        assert r_sec.status_code == 403, f"{path} was not blocked!"

    # 7. Block Google Login as Admin
    print("\n[TEST 7] Blocking Google Login as Admin (POST /api/auth/google)...")
    r_g_admin = client.post("/api/auth/google", json={
        "name": "Google Admin Attempt",
        "email": ADMIN_EMAIL,
        "role": "admin"
    })
    print("   Status Code:", r_g_admin.status_code)
    assert r_g_admin.status_code == 403, "Google login as admin was not blocked!"

    # 8. Live Database Admin Dashboard Verification
    print("\n[TEST 8] Admin Dashboard Live Supabase Data (GET /api/admin/analytics)...")
    r_dash = client.get("/api/admin/analytics", headers=admin_headers)
    print("   Status Code:", r_dash.status_code)
    assert r_dash.status_code == 200
    dash_data = r_dash.json()
    print("   Live Total Users Count in Supabase        :", dash_data.get("total_users"))
    print("   Live Total Schemes Count in Supabase      :", dash_data.get("total_schemes"))
    print("   Live Total Applications Count in Supabase :", dash_data.get("total_applications"))

    # 9. Real-Time Admin CRUD Verification (Delete User immediately updates Supabase)
    print("\n[TEST 9] Real-Time Admin CRUD Synchronization (Deleting citizen from Supabase)...")
    created_cit_id = r_c_login.json().get("user_id")
    r_del = client.delete(f"/api/admin/users/{created_cit_id}", headers=admin_headers)
    print("   Delete User Status Code:", r_del.status_code)
    assert r_del.status_code == 200

    # Verify user no longer exists in Supabase
    verif_users = db.fetch_rows("users", {"id": created_cit_id})
    print(f"   Remaining rows in Supabase for user '{created_cit_id}': {len(verif_users)}")
    assert len(verif_users) == 0, "User was not immediately deleted from Supabase!"

    # Final Admin Count check
    final_users = db.fetch_rows("users")
    final_admin_count = len([u for u in final_users if u.get("role") == "admin"])
    print(f"\n[FINAL ADMIN COUNT CHECK] SELECT COUNT(*) FROM users WHERE role='admin' -> {final_admin_count}")
    assert final_admin_count == 1, "Final admin count is not 1!"

    print("\n" + "=" * 80)
    print("[OK] DATABASE-BACKED SINGLE ADMINISTRATOR VERIFICATION COMPLETE!")
    print("=" * 80)

if __name__ == "__main__":
    verify_database_backed_single_admin()
