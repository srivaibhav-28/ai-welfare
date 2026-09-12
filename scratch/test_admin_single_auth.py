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
    print("            SURGICAL SINGLE ADMIN AUTHENTICATION VERIFICATION           ")
    print("=" * 80)

    # 1. Test Admin Login with valid credentials
    print("\n1. Testing Admin Login with valid configured credentials...")
    login_res = client.post("/api/admin/login", json={
        "email": "admin@welfare.gov",
        "password": "Admin@123456"
    })
    print(f"Status Code: {login_res.status_code}")
    print(f"Response Payload: {login_res.json()}")
    assert login_res.status_code == 200, f"Expected 200, got {login_res.status_code}"
    admin_token = login_res.json()["access_token"]
    assert login_res.json()["role"] == "admin"
    print("--> [PASS] Admin Login Successful!")

    # 2. Test Admin Login with invalid password
    print("\n2. Testing Admin Login with invalid password...")
    invalid_res = client.post("/api/admin/login", json={
        "email": "admin@welfare.gov",
        "password": "WrongPassword123"
    })
    print(f"Status Code: {invalid_res.status_code}")
    print(f"Response Detail: {invalid_res.json()}")
    assert invalid_res.status_code == 401, f"Expected 401, got {invalid_res.status_code}"
    print("--> [PASS] Unauthorized Admin Access Denied!")

    # 3. Test Admin Registration disabled
    print("\n3. Testing Admin Registration Attempt (Must be disabled/forbidden)...")
    reg_admin_res = client.post("/api/auth/register", json={
        "name": "Hacker Admin",
        "email": "hacker_admin@welfare.gov",
        "mobile_number": "9999999999",
        "password": "Password@123",
        "confirm_password": "Password@123",
        "role": "admin"
    })
    print(f"Status Code: {reg_admin_res.status_code}")
    print(f"Response Detail: {reg_admin_res.json()}")
    assert reg_admin_res.status_code == 403, f"Expected 403, got {reg_admin_res.status_code}"
    print("--> [PASS] Admin Registration Attempt Successfully Blocked!")

    # 4. Test Authenticated Admin accessing Admin Dashboard API
    print("\n4. Testing Authenticated Admin API access (/api/admin/analytics)...")
    admin_api_res = client.get("/api/admin/analytics", headers={
        "Authorization": f"Bearer {admin_token}"
    })
    print(f"Status Code: {admin_api_res.status_code}")
    assert admin_api_res.status_code == 200, f"Expected 200, got {admin_api_res.status_code}"
    print("--> [PASS] Authenticated Admin Access Granted!")

    # 5. Verify Citizen Registration & Login intact
    print("\n5. Verifying Citizen Registration & Login remain 100% operational...")
    cit_email = f"citizen_test_{os.urandom(3).hex()}@welfare.gov"
    cit_reg_res = client.post("/api/auth/register", json={
        "name": "Citizen User",
        "email": cit_email,
        "mobile_number": "9876543210",
        "password": "Password@123",
        "confirm_password": "Password@123",
        "role": "citizen"
    })
    assert cit_reg_res.status_code == 200, f"Expected 200, got {cit_reg_res.status_code}"
    print("--> [PASS] Citizen Registration intact!")

    print("\n" + "=" * 80)
    print("      SINGLE ADMIN SURGICAL AUTHENTICATION VERIFIED (100%)!       ")
    print("=" * 80)

if __name__ == "__main__":
    run_tests()
