import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath("."))

from fastapi.testclient import TestClient
from run import app
from app.database.supabase_db import db

client = TestClient(app)

def run_tests():
    print("=" * 80)
    print("        SURGICAL ADMIN DATABASE INTEGRATION VERIFICATION            ")
    print("=" * 80)

    # 1. Admin Login
    print("\n1. Admin Login...")
    admin_login_res = client.post("/api/admin/login", json={
        "email": "admin@welfare.gov",
        "password": "Admin@123456"
    })
    assert admin_login_res.status_code == 200, f"Failed admin login: {admin_login_res.text}"
    admin_token = admin_login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {admin_token}"}
    print("--> [PASS] Admin Authenticated!")

    # 2. Register & Verify OTP for a new test citizen user
    cit_email = f"db_integration_{os.urandom(3).hex()}@welfare.gov"
    print(f"\n2. Registering & Verifying new citizen user: {cit_email}...")
    reg_res = client.post("/api/auth/register", json={
        "name": "Integration User",
        "email": cit_email,
        "mobile_number": "9876543210",
        "password": "Password@123",
        "confirm_password": "Password@123",
        "role": "citizen"
    })
    assert reg_res.status_code == 200, f"Registration failed: {reg_res.text}"
    
    # Verify OTP
    otp = reg_res.json().get("otp", "123456")
    verify_res = client.post("/api/auth/verify-otp", json={
        "email": cit_email,
        "otp": otp
    })
    assert verify_res.status_code == 200, f"OTP verification failed: {verify_res.text}"
    
    v_data = verify_res.json()
    user_id = v_data.get("user_id") or v_data.get("id")
    assert user_id is not None, f"User ID is None in verify response: {v_data}"
    print(f"--> [PASS] Citizen Registered & Verified in DB with ID: {user_id}")

    # 3. Verify Admin reads LIVE users from public.users
    print("\n3. Admin fetching LIVE users list from /api/admin/users...")
    admin_users_res = client.get("/api/admin/users", headers=headers)
    assert admin_users_res.status_code == 200, f"Failed fetching users: {admin_users_res.text}"
    users_list = admin_users_res.json()
    user_ids = [u["id"] for u in users_list]
    assert user_id in user_ids, f"Newly created user {user_id} not found in Admin users list!"
    print(f"--> [PASS] Live user list confirmed! Found {len(users_list)} users.")

    # 4. Admin Block & Unblock User in public.users
    print(f"\n4. Admin blocking user {user_id} in public.users...")
    block_res = client.put(f"/api/admin/users/{user_id}/status", json={"is_blocked": True}, headers=headers)
    assert block_res.status_code == 200, f"Block failed: {block_res.text}"
    updated_user = db.get_user_by_id(user_id)
    assert updated_user.get("is_blocked") is True, "User is_blocked was not updated in DB!"
    print("--> [PASS] User successfully blocked in DB!")

    print(f"\n5. Admin unblocking user {user_id} in public.users...")
    unblock_res = client.put(f"/api/admin/users/{user_id}/status", json={"is_blocked": False}, headers=headers)
    assert unblock_res.status_code == 200, f"Unblock failed: {unblock_res.text}"
    updated_user = db.get_user_by_id(user_id)
    assert updated_user.get("is_blocked") is False, "User is_blocked was not updated in DB!"
    print("--> [PASS] User successfully unblocked in DB!")

    # 5. Admin Create & Delete Scheme in public.schemes
    scheme_name = f"Test Scheme {os.urandom(2).hex()}"
    print(f"\n6. Admin creating scheme '{scheme_name}' in public.schemes...")
    create_scheme_res = client.post("/api/admin/schemes", json={
        "name": scheme_name,
        "category": "Education",
        "description": "Integration Test Scheme",
        "benefits": "₹10,000 grant",
        "criteria": {"student_status": True},
        "required_documents": ["Student ID"],
        "official_link": "https://education.gov.in"
    }, headers=headers)
    assert create_scheme_res.status_code == 200, f"Scheme creation failed: {create_scheme_res.text}"
    created_scheme = create_scheme_res.json()["scheme"]
    scheme_id = created_scheme["id"]
    print(f"--> [PASS] Scheme created in DB with ID: {scheme_id}")

    print(f"\n7. Admin deleting scheme {scheme_id} from public.schemes...")
    del_scheme_res = client.delete(f"/api/admin/schemes/{scheme_id}", headers=headers)
    assert del_scheme_res.status_code == 200, f"Scheme deletion failed: {del_scheme_res.text}"
    assert db.get_scheme_by_id(scheme_id) is None, "Scheme still exists in DB!"
    print("--> [PASS] Scheme deleted from DB!")

    # 6. Admin Delete User from public.users
    print(f"\n8. Admin deleting user {user_id} from public.users...")
    del_user_res = client.delete(f"/api/admin/users/{user_id}", headers=headers)
    assert del_user_res.status_code == 200, f"User deletion failed: {del_user_res.text}"
    assert db.get_user_by_id(user_id) is None, "User still exists in DB after deletion!"
    print("--> [PASS] User deleted from DB!")

    # 7. Verify Admin Analytics Endpoint returns live production stats
    print("\n9. Admin Analytics LIVE data check...")
    analytics_res = client.get("/api/admin/analytics", headers=headers)
    assert analytics_res.status_code == 200, f"Analytics failed: {analytics_res.text}"
    data = analytics_res.json()
    assert "total_users" in data and "total_applications" in data, "Invalid analytics response"
    print(f"--> [PASS] Live Analytics verified! Total Users: {data['total_users']}, Total Applications: {data['total_applications']}")

    print("\n" + "=" * 80)
    print("   SURGICAL ADMIN DATABASE INTEGRATION VERIFIED 100% OPERATIONAL!   ")
    print("=" * 80)

if __name__ == "__main__":
    run_tests()
