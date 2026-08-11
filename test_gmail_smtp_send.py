from app.services.email_service import EmailNotificationService

def test_send():
    print("Testing Gmail SMTP email dispatch...")
    to_email = "aiwelfareeligibilitychecker@gmail.com"
    subject = "Test OTP Email Dispatch"
    body_html = "<h1>Your 6-digit OTP code is: 889900</h1>"
    body_text = "Your 6-digit OTP code is: 889900"

    success, msg = EmailNotificationService.send_email(to_email, subject, body_html, body_text)
    print(f"Success: {success}")
    print(f"Detail: {msg}")

if __name__ == "__main__":
    test_send()
