import requests
import json
import uuid

BASE_URL = "http://127.0.0.1:8000"

def run_payload_test():
    print("=" * 80)
    print("        REGISTRATION PAYLOAD DUMP & EXACT FIELD AUDIT TEST        ")
    print("=" * 80)

    test_email = f"payload_check_{uuid.uuid4().hex[:6]}@gmail.com"
    pwd = "SecurePassword@123"

    frontend_payload = {
        "name": "Audit User",
        "email": test_email,
        "mobile_number": "9876543210",
        "password": pwd,
        "confirm_password": pwd,
        "role": "citizen"
    }

    print("\n--- FRONTEND JSON PAYLOAD ---")
    print("[API REGISTRATION PAYLOAD]")
    print(json.dumps(frontend_payload, indent=2))
    print(f"Frontend password        = '{frontend_payload['password']}'")
    print(f"Frontend confirm_password= '{frontend_payload['confirm_password']}'")
    print(f"Frontend confirmPassword = undefined (NOT USED)")

    print("\n--- SENDING REGISTRATION REQUEST (POST /api/auth/register) ---")
    res = requests.post(f"{BASE_URL}/api/auth/register", json=frontend_payload)

    print(f"\n--- BACKEND RESPONSE ---")
    print(f"HTTP Status Code: {res.status_code}")
    print(f"Response JSON   : {json.dumps(res.json(), indent=2)}")

    print("\n" + "=" * 80)

if __name__ == "__main__":
    run_payload_test()
