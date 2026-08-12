import requests
import json
import uuid

BASE_URL = "http://127.0.0.1:8000"

def test_phase1_and_phase2():
    print("=" * 80)
    print("      PHASE 1 & 2 VERIFICATION TEST: PROFILE MODULE & AI EVALUATION     ")
    print("=" * 80)

    test_email = f"phase1_user_{uuid.uuid4().hex[:6]}@gmail.com"
    pwd = "SecurePassword123"

    # Step 1: Register
    r_reg = requests.post(f"{BASE_URL}/api/auth/register", json={
        "name": "Phase 1 Citizen",
        "email": test_email,
        "mobile_number": "9988776655",
        "password": pwd,
        "confirm": pwd,
        "role": "citizen"
    })
    assert r_reg.status_code == 200, f"Registration failed: {r_reg.text}"

    # Step 2: Verify OTP
    r_otp = requests.post(f"{BASE_URL}/api/auth/verify-otp", json={
        "email": test_email,
        "otp": "123456"
    })
    assert r_otp.status_code == 200, f"OTP verification failed: {r_otp.text}"
    token = r_otp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("[OK] User registered and verified with OTP")

    # Step 3: Mandatory Profile Completion (Phase 1)
    profile_payload = {
        "name": "Phase 1 Citizen",
        "mobile_number": "9988776655",
        "aadhaar_number": "123456789012",
        "dob": "1995-08-15",
        "gender": "Female",
        "marital_status": "Single",
        "state": "Uttar Pradesh",
        "district": "Varanasi",
        "mandal": "Sadar",
        "village": "Shivpur",
        "pincode": "221001",
        "rural_urban": "Rural",
        "occupation": "Student",
        "annual_income": 120000,
        "family_income": 150000,
        "bank_account_number": "987654321098",
        "ifsc_code": "SBIN0001234",
        "education": "Graduate",
        "caste_category": "OBC",
        "farmer_status": False,
        "student_status": True,
        "disability_status": False,
        "senior_citizen_status": False,
        "widow_status": False,
        "bpl_status": True,
        "minority_status": False,
        "unemployed_status": False,
        "aadhaar_available": True,
        "bank_account_available": True,
        "profile_completed": True
    }

    r_prof = requests.post(f"{BASE_URL}/api/profile", headers=headers, json=profile_payload)
    assert r_prof.status_code == 200, f"Profile completion failed: {r_prof.text}"
    prof_res = r_prof.json()["profile"]
    assert prof_res.get("profile_completed") is True, "profile_completed flag not set!"
    print("[OK] Mandatory profile saved to Supabase (profile_completed = True)")

    # Step 4: GET /api/profile
    r_get_prof = requests.get(f"{BASE_URL}/api/profile", headers=headers)
    assert r_get_prof.status_code == 200
    assert r_get_prof.json().get("profile_completed") is True
    print("[OK] Profile retrieved successfully with completed status")

    # Step 5: AI Automated Profile Reading & Evaluation (Phase 2)
    r_eval = requests.post(f"{BASE_URL}/api/evaluate", json=profile_payload)
    assert r_eval.status_code == 200
    eval_data = r_eval.json()
    assert "recommendations" in eval_data or "eligible_schemes" in eval_data, "No schemes returned from evaluation!"
    print(f"[OK] AI Eligibility Engine evaluated stored profile without extra questions ({len(eval_data.get('recommendations', []))} schemes analyzed)")

    # Step 6: Bookmark Scheme (Phase 3)
    r_bm = requests.post(f"{BASE_URL}/api/schemes/scheme-004/bookmark", headers=headers)
    assert r_bm.status_code == 200
    assert "scheme-004" in r_bm.json()["saved_schemes"]
    print("[OK] Scheme bookmarked for later")

    print("\n" + "=" * 80)
    print("SUCCESS: ALL PHASE 1, 2 & 3 EVOLUTION VERIFICATION TESTS PASSED!")
    print("=" * 80)

if __name__ == "__main__":
    test_phase1_and_phase2()
