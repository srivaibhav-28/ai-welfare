import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath("."))

from fastapi.testclient import TestClient
from run import app

client = TestClient(app)

def run_verification():
    print("=" * 80)
    print("        VERIFYING /api/admin/login ENDPOINT & OPENAPI SCHEMA         ")
    print("=" * 80)

    # 1. Fetch openapi.json
    print("\n1. GET /openapi.json...")
    res_openapi = client.get("/openapi.json")
    assert res_openapi.status_code == 200, f"openapi.json failed: {res_openapi.text}"
    openapi_data = res_openapi.json()
    paths = openapi_data.get("paths", {})
    assert "/api/admin/login" in paths, "POST /api/admin/login NOT found in /openapi.json!"
    print("--> [PASS] /openapi.json contains '/api/admin/login'!")

    # 2. Test POST /api/admin/login with correct credentials
    print("\n2. POST /api/admin/login (Valid Credentials)...")
    res_login = client.post("/api/admin/login", json={
        "email": "admin@welfare.gov",
        "password": "Admin@123456"
    })
    assert res_login.status_code == 200, f"Admin login failed: {res_login.text}"
    data = res_login.json()
    assert "access_token" in data and data.get("role") == "admin", f"Invalid response: {data}"
    print(f"--> [PASS] Admin Login successful! Token issued for {data['email']}")

    # 3. Test POST /api/admin/login with invalid credentials
    print("\n3. POST /api/admin/login (Invalid Credentials)...")
    res_invalid = client.post("/api/admin/login", json={
        "email": "admin@welfare.gov",
        "password": "WrongPassword"
    })
    assert res_invalid.status_code == 401, f"Expected 401 Unauthorized, got {res_invalid.status_code}"
    print("--> [PASS] Invalid password correctly rejected with 401 Unauthorized!")

    print("\n" + "=" * 80)
    print("        404 FIX VERIFIED 100% SUCCESSFUL!                            ")
    print("=" * 80)

if __name__ == "__main__":
    run_verification()
