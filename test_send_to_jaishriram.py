import requests
from app.services.email_service import EmailNotificationService

def test_jaishriram():
    print("=" * 80)
    print("TESTING GMAIL SMTP DISPATCH TO jaishriramram1122@gmail.com")
    print("=" * 80)

    target_email = "jaishriramram1122@gmail.com"
    otp_code = "778899"

    success, msg = EmailNotificationService.send_registration_otp(target_email, otp_code)
    print(f"SMTP Dispatch Result : {success}")
    print(f"SMTP Dispatch Detail : {msg}")
    print("=" * 80)

if __name__ == "__main__":
    test_jaishriram()
