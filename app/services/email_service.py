import os
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

def safe_print(*args, **kwargs):
    try:
        print(*args, **kwargs)
    except Exception:
        safe_args = [str(a).encode('ascii', 'ignore').decode('ascii') for a in args]
        try:
            print(*safe_args, **kwargs)
        except Exception:
            pass

class EmailNotificationService:
    @staticmethod
    def send_email(to_email: str, subject: str, body_html: str, body_text: str = "") -> Tuple[bool, str]:
        """
        Email Notification Service with Resend API + SMTP + Console Fallback.
        Returns (success: bool, detail: str).
        """
        safe_print("=" * 80)
        safe_print(f"[EMAIL STEP 1] Executing Email Dispatch to: {to_email}")
        safe_print(f"[EMAIL STEP 2] Subject: {subject}")

        resend_api_key = os.getenv("RESEND_API_KEY")
        smtp_user = os.getenv("SMTP_USER") or "aiwelfareeligibilitychecker@gmail.com"
        smtp_password = os.getenv("SMTP_PASSWORD") or "wmtyhrvezwhuamvx"
        smtp_host = os.getenv("SMTP_HOST") or "smtp.gmail.com"
        smtp_port = int(os.getenv("SMTP_PORT") or "587")

        # Provider Strategy 1: Resend HTTP API
        if resend_api_key:
            safe_print(f"[EMAIL STEP 3] Provider Selected: Resend HTTP API")
            try:
                from_email = os.getenv("RESEND_FROM_EMAIL", "Welfare Portal <onboarding@resend.dev>")
                res = requests.post(
                    "https://api.resend.com/emails",
                    headers={
                        "Authorization": f"Bearer {resend_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "from": from_email,
                        "to": [to_email],
                        "subject": subject,
                        "html": body_html,
                        "text": body_text or body_html
                    },
                    timeout=12
                )
                safe_print(f"[EMAIL STEP 4] Resend API Response Status: {res.status_code}")
                if res.status_code in [200, 201]:
                    msg_id = res.json().get('id', 'resend-ok')
                    safe_print(f"[EMAIL SUCCESS] Delivered to {to_email} via Resend API | ID: {msg_id}")
                    safe_print("=" * 80)
                    return True, f"Delivered via Resend API (ID: {msg_id})"
                else:
                    err_msg = res.text
                    safe_print(f"[EMAIL FAILURE] Resend API Error Status {res.status_code}: {err_msg}")
                    safe_print("=" * 80)
                    return False, f"Resend API Error ({res.status_code}): {err_msg}"
            except Exception as e:
                safe_print(f"[EMAIL EXCEPTION] Resend API Call Failed: {e}")
                return False, f"Resend API Exception: {str(e)}"

        # Provider Strategy 2: SMTP (Gmail / Custom SMTP Server)
        if smtp_user and smtp_password:
            safe_print(f"[EMAIL STEP 3] Provider Selected: SMTP ({smtp_host}:{smtp_port})")
            try:
                msg = MIMEMultipart("alternative")
                msg["Subject"] = subject
                msg["From"] = os.getenv("SMTP_FROM_EMAIL", smtp_user)
                msg["To"] = to_email

                part1 = MIMEText(body_text or body_html, "plain")
                part2 = MIMEText(body_html, "html")
                msg.attach(part1)
                msg.attach(part2)

                server = smtplib.SMTP(smtp_host, smtp_port, timeout=15)
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(smtp_user, smtp_password)
                safe_print("SMTP Login Success")
                server.sendmail(smtp_user, [to_email], msg.as_string())
                server.quit()
                safe_print("Email Sent")
                safe_print(f"Recipient: {to_email}")
                safe_print(f"[EMAIL SUCCESS] Delivered to {to_email} via SMTP ({smtp_host})")
                safe_print("=" * 80)
                return True, f"Delivered via Gmail SMTP ({smtp_host})"
            except smtplib.SMTPAuthenticationError as e:
                err = f"Gmail SMTP Authentication Failed: Invalid email or App Password. Detail: {e}"
                safe_print(f"[EMAIL FAILURE] {err}")
                safe_print("=" * 80)
                return False, err
            except smtplib.SMTPException as e:
                err = f"Gmail SMTP Error: {e}"
                safe_print(f"[EMAIL FAILURE] {err}")
                safe_print("=" * 80)
                return False, err
            except Exception as e:
                err = f"SMTP Connection/Send Error: {type(e).__name__}: {e}"
                safe_print(f"[EMAIL EXCEPTION] {err}")
                safe_print("=" * 80)
                return False, err

        # Provider Strategy 3: Local Dev Console Log Mode
        safe_print(f"[EMAIL STEP 3] No RESEND_API_KEY or SMTP_USER found in environment variables.")
        safe_print(f"[EMAIL STEP 4] Operating in Local Console Simulation Mode.")
        safe_print("-" * 70)
        safe_print((body_text or body_html).encode('ascii', 'ignore').decode('ascii'))
        safe_print("=" * 80)
        return True, "Simulated Dispatch (Console Log Mode - Set RESEND_API_KEY for live delivery)"

    @classmethod
    def send_registration_otp(cls, to_email: str, otp_code: str) -> Tuple[bool, str]:
        subject = "🔐 Government Welfare Portal - Email Verification OTP"
        body_html = f"""
        <div style="font-family: Arial, sans-serif; padding: 20px; color: #1e293b;">
            <h2 style="color: #ea580c;">National Welfare Portal Identity Verification</h2>
            <p>Dear Citizen,</p>
            <p>Your one-time email verification code (OTP) is:</p>
            <div style="background: #fff7ed; border: 2px dashed #f97316; padding: 15px; text-align: center; font-size: 28px; font-weight: bold; letter-spacing: 5px; color: #c2410c; margin: 15px 0;">
                {otp_code}
            </div>
            <p>This OTP code is valid for 15 minutes. Please do not share this code with anyone.</p>
            <p style="font-size: 12px; color: #64748b;">Ministry of Electronics & IT | Government of India</p>
        </div>
        """
        body_text = f"Your Government Welfare Portal verification OTP is: {otp_code}. Valid for 15 minutes."
        return cls.send_email(to_email, subject, body_html, body_text)

    @classmethod
    def send_application_otp(cls, to_email: str, scheme_name: str, otp_code: str) -> Tuple[bool, str]:
        subject = "🔐 Application Security Verification OTP - National Welfare Portal"
        body_html = f"""
        <div style="font-family: Arial, sans-serif; padding: 20px; color: #1e293b; line-height: 1.6;">
            <h2 style="color: #4f46e5;">Application Submission Security OTP</h2>
            <p>Dear Applicant,</p>
            <p>Your 6-digit verification code to confirm submission for scheme <strong>{scheme_name}</strong> is:</p>
            <div style="background: #eff6ff; border: 2px dashed #3b82f6; padding: 15px; text-align: center; font-size: 28px; font-weight: bold; letter-spacing: 5px; color: #1d4ed8; margin: 15px 0; border-radius: 8px;">
                {otp_code}
            </div>
            <p>This OTP code is valid for <strong>5 minutes</strong>. Please enter this code into the portal to complete your application submission.</p>
            <br/>
            <p>Regards,<br/><strong>AI Government Welfare Eligibility Assistant</strong></p>
        </div>
        """
        body_text = f"Dear Applicant,\n\nYour 6-digit verification code to confirm submission for scheme '{scheme_name}' is: {otp_code}.\n\nThis OTP code is valid for 5 minutes.\n\nRegards,\nAI Government Welfare Eligibility Assistant"
        return cls.send_email(to_email, subject, body_html, body_text)

    @classmethod
    def send_application_submitted(cls, to_email: str, app_id: str, scheme_name: str, applicant_name: str = "Applicant", submission_date: str = "") -> Tuple[bool, str]:
        subject = "Application Submitted Successfully"
        date_str = submission_date or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        body_html = f"""
        <div style="font-family: Arial, sans-serif; padding: 20px; color: #1e293b; line-height: 1.6;">
            <p>Dear <strong>{applicant_name}</strong>,</p>
            <p>Your application has been submitted successfully.</p>
            <table style="width: 100%; border-collapse: collapse; margin: 15px 0; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px;">
                <tr><td style="padding: 10px; border-bottom: 1px solid #e2e8f0; font-weight: bold; width: 140px;">Application ID:</td><td style="padding: 10px; border-bottom: 1px solid #e2e8f0; font-family: monospace; font-weight: bold; color: #4f46e5;">{app_id}</td></tr>
                <tr><td style="padding: 10px; border-bottom: 1px solid #e2e8f0; font-weight: bold;">Scheme Name:</td><td style="padding: 10px; border-bottom: 1px solid #e2e8f0;">{scheme_name}</td></tr>
                <tr><td style="padding: 10px; border-bottom: 1px solid #e2e8f0; font-weight: bold;">Submission Date:</td><td style="padding: 10px; border-bottom: 1px solid #e2e8f0;">{date_str}</td></tr>
                <tr><td style="padding: 10px; font-weight: bold;">Current Status:</td><td style="padding: 10px; color: #d97706; font-weight: bold;">Submitted</td></tr>
            </table>
            <p>You can track your application anytime from the <strong>Application Tracker</strong> on your dashboard portal.</p>
            <br/>
            <p>Regards,<br/><strong>AI Government Welfare Eligibility Assistant</strong></p>
        </div>
        """
        body_text = f"Dear {applicant_name},\n\nYour application has been submitted successfully.\n\nApplication ID: {app_id}\nScheme Name: {scheme_name}\nSubmission Date: {date_str}\nCurrent Status: Submitted\n\nYou can track your application anytime from the Application Tracker.\n\nRegards,\nAI Government Welfare Eligibility Assistant"
        return cls.send_email(to_email, subject, body_html, body_text)

    @classmethod
    def send_status_update(cls, to_email: str, app_id: str, scheme_name: str, status: str, remarks: str = "") -> bool:
        subject = f"🔔 Application Status Update ({status}): {app_id}"
        status_color = "#16a34a" if status == "Approved" else ("#dc2626" if status == "Rejected" else "#ca8a04")
        body_html = f"""
        <div style="font-family: Arial, sans-serif; padding: 20px; color: #1e293b;">
            <h2 style="color: {status_color};">Application Status Updated: {status}</h2>
            <p>The status of your welfare application has been updated by the verification officer.</p>
            <ul style="list-style: none; padding: 0;">
                <li><strong>Application ID:</strong> {app_id}</li>
                <li><strong>Scheme:</strong> {scheme_name}</li>
                <li><strong>New Status:</strong> <span style="color: {status_color}; font-weight: bold;">{status}</span></li>
                <li><strong>Remarks:</strong> {remarks or 'No additional remarks.'}</li>
            </ul>
        </div>
        """
        body_text = f"Application Update: {app_id} for {scheme_name} is now {status}. Remarks: {remarks}"
        return cls.send_email(to_email, subject, body_html, body_text)

    @classmethod
    def send_deadline_reminder(cls, to_email: str, scheme_name: str, days_left: int) -> bool:
        subject = f"⏳ Action Required: {scheme_name} Closes in {days_left} Days"
        body_html = f"""
        <div style="font-family: Arial, sans-serif; padding: 20px; color: #1e293b;">
            <h2 style="color: #eab308;">Upcoming Scheme Deadline Alert</h2>
            <p>This is a reminder that applications for <strong>{scheme_name}</strong> will close in <strong>{days_left} days</strong>.</p>
            <p>Please log in to your portal and submit your application along with required JPEG documents before the deadline.</p>
        </div>
        """
        body_text = f"Deadline Alert: {scheme_name} closes in {days_left} days. Complete your application now."
        return cls.send_email(to_email, subject, body_html, body_text)
