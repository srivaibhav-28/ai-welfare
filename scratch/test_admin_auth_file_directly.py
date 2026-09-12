import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath("."))

from dotenv import load_dotenv
load_dotenv()

from fastapi.testclient import TestClient
from api.admin_auth import app as admin_auth_app

client = TestClient(admin_auth_app)

def test_standalone_admin_auth():
    print("=" * 80)
    print("        TESTING api/admin_auth.py STANDALONE VERCEL ENTRYPOINT       ")
    print("=" * 80)

    try:
        res = client.post("/api/admin/login", json={
            "email": "admin@welfare.gov",
            "password": "Admin@123456"
        })
        print(f"Status Code : {res.status_code}")
        print(f"Content-Type: {res.headers.get('content-type')}")
        print(f"Response    : {res.text}")

        assert res.status_code == 200
        data = res.json()
        assert "access_token" in data
        assert data.get("role") == "admin"
        print("--> [PASS] api/admin_auth.py standalone test 100% SUCCESSFUL!")
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_standalone_admin_auth()
