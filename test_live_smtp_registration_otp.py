import requests

BASE_URL = "http://127.0.0.1:8000"

def test_live_otp():
    print("=" * 80)
    print("TESTING LIVE REGISTRATION & OTP DISPATCH VIA GMAIL SMTP")
    print("=" * 80)

    test_email = "vaibhav.test99@gmail.com"
    r = requests.post(f"{BASE_URL}/api/auth/register", json={
        "name": "Vaibhav Test",
        "email": test_email,
        "mobile_number": "9876543210",
        "password": "Password123",
        "confirm_password": "Password123",
        "role": "citizen"
    })

    print("Register Status Code:", r.status_code)
    print("Register Response Body:", r.json())
    print("=" * 80)

if __name__ == "__main__":
    test_live_otp()
