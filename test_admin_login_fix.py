import requests

BASE_URL = "http://127.0.0.1:8000"

def test_logins():
    print("=" * 80)
    print("TESTING ADMIN LOGIN FIXES")
    print("=" * 80)

    # Test 1: Default Admin 1
    r1 = requests.post(f"{BASE_URL}/api/admin/login", json={"email": "admin@aiwelfare.gov", "password": "Admin@123"})
    print("1. admin@aiwelfare.gov Status Code:", r1.status_code)
    if r1.status_code == 200:
        print("   Token:", r1.json().get("access_token")[:30] + "...")

    # Test 2: Default Admin 2
    r2 = requests.post(f"{BASE_URL}/api/admin/login", json={"email": "admin@welfare.gov", "password": "admin123"})
    print("2. admin@welfare.gov Status Code:", r2.status_code)

    # Test 3: Favicon route
    rf = requests.get(f"{BASE_URL}/favicon.ico")
    print("3. /favicon.ico Status Code:", rf.status_code, "(Should be 204 No Content)")

    print("=" * 80)

if __name__ == "__main__":
    test_logins()
