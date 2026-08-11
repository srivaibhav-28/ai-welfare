import requests

BASE_URL = "http://127.0.0.1:8000"

def test_otp():
    print("=" * 80)
    print("TESTING OTP DELIVERY TO vaibhav@gmail.com VIA GMAIL SMTP")
    print("=" * 80)

    # 1. Resend OTP to vaibhav@gmail.com
    r_send = requests.post(f"{BASE_URL}/api/auth/send-otp", json={"email": "vaibhav@gmail.com"})
    print("Send OTP Response Code:", r_send.status_code)
    print("Send OTP Response Body:", r_send.json())

    print("=" * 80)

if __name__ == "__main__":
    test_otp()
