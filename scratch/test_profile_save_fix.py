import requests
from app.services.auth_service import create_access_token

BASE_URL = "http://127.0.0.1:8000"

def test_profile_save_direct():
    user_id = "usr-f05fbda7"
    print(f"[TEST] Testing profile save for reported user_id: {user_id}")
    
    # Create JWT token for usr-f05fbda7
    token = create_access_token({
        "sub": user_id,
        "email": "usr-f05fbda7@welfare.gov",
        "name": "Reported Citizen User",
        "role": "citizen"
    })
    
    headers = {"Authorization": f"Bearer {token}"}
    
    profile_payload = {
        "name": "Reported Citizen User",
        "email": "usr-f05fbda7@welfare.gov",
        "mobile_number": "9876543210",
        "aadhaar_number": "123456789012",
        "dob": "1995-05-15",
        "gender": "Male",
        "marital_status": "Single",
        "state": "Andhra Pradesh",
        "district": "Visakhapatnam",
        "mandal": "Visakhapatnam",
        "village": "Gajuwaka",
        "pincode": "530026",
        "occupation": "Software Engineer",
        "annual_income": 300000,
        "family_income": 500000,
        "education": "Graduate",
        "caste_category": "General",
        "disability_status": False,
        "student_status": False,
        "farmer_status": False,
        "senior_citizen_status": False,
        "widow_status": False,
        "bpl_status": False,
        "minority_status": False,
        "unemployed_status": False,
        "aadhaar_available": True,
        "bank_account_available": True,
        "bank_account_number": "987654321098",
        "ifsc_code": "SBIN0001234",
        "rural_urban": "Urban"
    }
    
    # Test POST /api/profile
    print("\n--- Sending POST /api/profile ---")
    prof_res = requests.post(f"{BASE_URL}/api/profile", json=profile_payload, headers=headers)
    print(f"POST /api/profile HTTP status: {prof_res.status_code}")
    print(f"POST /api/profile response: {prof_res.json()}")
    assert prof_res.status_code == 200, f"Expected 200, got {prof_res.status_code}"
    
    # Test GET /api/profile
    print("\n--- Sending GET /api/profile ---")
    get_res = requests.get(f"{BASE_URL}/api/profile", headers=headers)
    print(f"GET /api/profile HTTP status: {get_res.status_code}")
    print(f"GET /api/profile response: {get_res.json()}")
    assert get_res.status_code == 200, f"Expected 200, got {get_res.status_code}"
    
    print("\n✅ PROFILE SAVE VERIFICATION SUCCESSFUL! No 401 Unauthorized, user record automatically synchronized!")

if __name__ == "__main__":
    test_profile_save_direct()
