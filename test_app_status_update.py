import requests

BASE_URL = "http://127.0.0.1:8000"

def test_status_update():
    # Login as admin
    r_login = requests.post(f"{BASE_URL}/api/admin/login", json={"email": "admin@aiwelfare.gov", "password": "Admin@123"})
    print("Admin Login Status:", r_login.status_code)
    token = r_login.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}

    # Submit a test application first
    r_reg = requests.post(f"{BASE_URL}/api/auth/register", json={
        "name": "App Test Citizen",
        "email": "apptest_citizen@gmail.com",
        "mobile_number": "9876543210",
        "password": "Password123",
        "confirm_password": "Password123",
        "role": "citizen"
    })
    
    r_verify = requests.post(f"{BASE_URL}/api/auth/verify-otp", json={"email": "apptest_citizen@gmail.com", "otp": "123456"})
    c_token = r_verify.json().get("access_token")
    c_headers = {"Authorization": f"Bearer {c_token}"}

    # Submit application directly
    r_submit = requests.post(f"{BASE_URL}/api/applications/direct-apply", json={
        "scheme_id": "scheme-001",
        "uploaded_documents": {"Aadhaar Card": "aadhaar.jpg"}
    }, headers=c_headers)
    
    print("Application Direct Apply Status:", r_submit.status_code)
    app_data = r_submit.json().get("application", {})
    app_id = app_data.get("id")
    print(f"Created Application ID: {app_id}")

    if app_id:
        # Test PUT /api/applications/{app_id}/status
        r_update = requests.put(f"{BASE_URL}/api/applications/{app_id}/status", json={
            "status": "Approved",
            "remarks": "Approved during admin audit test"
        }, headers=headers)
        print("Update Application Status Code:", r_update.status_code)
        print("Update Application Response:", r_update.json())

if __name__ == "__main__":
    test_status_update()
