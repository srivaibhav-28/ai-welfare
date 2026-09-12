import os
import sys
import uuid

sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
from starlette.testclient import TestClient
from run import app
from app.database.supabase_db import db
from app.services.auth_service import hash_password, verify_password

client = TestClient(app)

def test_forgot_password_and_reset_flow():
    print("=" * 80)
    print("  FORGOT PASSWORD & SECURITY VERIFICATION TEST SUITE (PRODUCTION READY)  ")
    print("=" * 80)

    # 1. Create a test citizen user in Supabase / DB
    test_email = f"test_pwd_reset_{uuid.uuid4().hex[:6]}@welfare.gov"
    old_password = "OldPassword123!"
    new_password = "NewPassword456!"

    print(f"\n[TEST 1] Creating test user in Supabase ({test_email})...")
    test_user = {
        "id": f"usr-{uuid.uuid4().hex[:8]}",
        "email": test_email,
        "name": "Password Reset Test User",
        "mobile_number": "9876543210",
        "password_hash": hash_password(old_password),
        "role": "citizen",
        "is_verified": True
    }
    db.add_user(test_user)
    print(f"   User created with ID: {test_user['id']}")

    # 2. Verify Old Password Login Works
    print("\n[TEST 2] Verifying login with Old Password...")
    r_login_old = client.post("/api/auth/login", json={
        "email": test_email,
        "password": old_password
    })
    print("   Status Code:", r_login_old.status_code)
    assert r_login_old.status_code == 200, f"Old password login failed: {r_login_old.text}"
    print("   Old password login successful!")

    # 3. Request Password Reset for Non-Existent Email (Anti-Enumeration Check)
    print("\n[TEST 3] Request Password Reset for non-existent email (Anti-Enumeration Check)...")
    r_forgot_fake = client.post("/api/auth/forgot-password", json={
        "email": "non_existent_user_9999@welfare.gov"
    })
    print("   Status Code:", r_forgot_fake.status_code)
    assert r_forgot_fake.status_code == 200, "Anti-enumeration requires 200 OK!"
    res_fake = r_forgot_fake.json()
    print("   Response Payload:", res_fake)
    assert res_fake.get("success") is True, "Response must indicate success!"
    assert res_fake.get("reset_token") is None, "Reset token must NOT be returned in API response!"
    print("   Anti-enumeration verification passed!")

    # 4. Request Password Reset for Registered User (Token not exposed in API response)
    print("\n[TEST 4] Request Password Reset for registered user...")
    r_forgot = client.post("/api/auth/forgot-password", json={
        "email": test_email
    })
    print("   Status Code:", r_forgot.status_code)
    assert r_forgot.status_code == 200, f"Forgot password failed: {r_forgot.text}"
    res_forgot = r_forgot.json()
    print("   Response Payload:", res_forgot)
    assert res_forgot.get("success") is True, "Response must indicate success!"
    assert res_forgot.get("reset_token") is None, "Reset token must NOT be exposed in API response!"

    # Retrieve generated reset token from db store for verification test
    tokens_store = getattr(db, "_in_memory_reset_tokens", {})
    matching_tokens = [k for k, v in tokens_store.items() if v.get("email") == test_email and not v.get("used")]
    assert len(matching_tokens) > 0, "Reset token was not saved in DB store!"
    reset_token = matching_tokens[-1]
    print("   Token retrieved securely from DB store for test execution:", reset_token[:8] + "...")

    # 5. Reset Password with Invalid Token (Should return 400)
    print("\n[TEST 5] Reset password with invalid token...")
    r_invalid_token = client.post("/api/auth/reset-password", json={
        "email": test_email,
        "token": "invalid_fake_token_12345",
        "new_password": new_password
    })
    print("   Status Code:", r_invalid_token.status_code)
    assert r_invalid_token.status_code == 400, "Expected 400 for invalid token"
    print("   Invalid token rejection verified!")

    # 6. Reset Password with Valid Token and New Password (Should return 200)
    print("\n[TEST 6] Reset password with valid token...")
    r_reset = client.post("/api/auth/reset-password", json={
        "email": test_email,
        "token": reset_token,
        "new_password": new_password
    })
    print("   Status Code:", r_reset.status_code)
    assert r_reset.status_code == 200, f"Password reset failed: {r_reset.text}"
    print("   Password reset successful!")

    # 7. Attempt reuse of same token (Should return 400 - Single Use Security)
    print("\n[TEST 7] Attempting to reuse the same reset token (Single-Use Check)...")
    r_reuse = client.post("/api/auth/reset-password", json={
        "email": test_email,
        "token": reset_token,
        "new_password": "AnotherPassword789!"
    })
    print("   Status Code:", r_reuse.status_code)
    assert r_reuse.status_code == 400, "Token reuse should fail with 400!"
    print("   Single-use token enforcement verified!")

    # 8. Attempt login with Old Password (Should fail with 401)
    print("\n[TEST 8] Login attempt with Old Password after reset...")
    r_login_old_after = client.post("/api/auth/login", json={
        "email": test_email,
        "password": old_password
    })
    print("   Status Code:", r_login_old_after.status_code)
    assert r_login_old_after.status_code == 401, "Old password must fail after reset!"
    print("   Old password successfully invalidated!")

    # 9. Login attempt with New Password (Should succeed with 200)
    print("\n[TEST 9] Login attempt with New Password after reset...")
    r_login_new = client.post("/api/auth/login", json={
        "email": test_email,
        "password": new_password
    })
    print("   Status Code:", r_login_new.status_code)
    assert r_login_new.status_code == 200, f"New password login failed: {r_login_new.text}"
    print("   New password login successful!")

    # Cleanup test user from Supabase
    db.delete_user(test_user["id"])
    print(f"\n[CLEANUP] Deleted test user {test_user['id']} from database.")

    print("\n" + "=" * 80)
    print("  [SUCCESS] ALL FORGOT PASSWORD & SECURITY VERIFICATION TESTS PASSED!  ")
    print("=" * 80)

if __name__ == "__main__":
    test_forgot_password_and_reset_flow()
