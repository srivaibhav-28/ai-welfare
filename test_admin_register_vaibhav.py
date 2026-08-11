import requests

BASE_URL = "http://127.0.0.1:8000"

def test_admin_registration():
    print("=" * 80)
    print("TESTING ADMIN REGISTRATION FOR vaibhav@gmail.com")
    print("=" * 80)

    payload = {
        "name": "Vaibhav",
        "email": "vaibhav@gmail.com",
        "mobile_number": "9440638282",
        "password": "Password123",
        "confirm_password": "Password123",
        "role": "admin",
        "invite_code": "ADMIN2026"
    }

    r = requests.post(f"{BASE_URL}/api/auth/register", json=payload)
    print(f"Register Admin Status Code: {r.status_code}")
    print(f"Register Admin Response: {r.json()}")

    if r.status_code == 200:
        token = r.json().get("access_token")
        print(f"\nSuccessfully registered & verified admin account for vaibhav@gmail.com!")
        print(f"Token: {token[:30]}...")

        # Test login after registration
        r_login = requests.post(f"{BASE_URL}/api/admin/login", json={"email": "vaibhav@gmail.com", "password": "Password123"})
        print(f"\nAdmin Login Status Code: {r_login.status_code}")
        print(f"Admin Login Response Role: {r_login.json().get('role')}")

    print("=" * 80)

if __name__ == "__main__":
    test_admin_registration()
