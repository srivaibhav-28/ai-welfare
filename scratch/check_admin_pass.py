import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath("."))

from dotenv import load_dotenv
load_dotenv()

from app.services.auth_service import verify_password
from app.admin_constants import ADMIN_EMAIL, ADMIN_PASSWORD_HASH, authenticate_admin

def check():
    print("=" * 80)
    print("        ADMIN PASSWORD VERIFICATION INSPECTION                       ")
    print("=" * 80)

    print(f"ADMIN_EMAIL        : {ADMIN_EMAIL}")
    print(f"ADMIN_PASSWORD_HASH: {ADMIN_PASSWORD_HASH}")

    passwords_to_test = [
        "Admin@123456",
        "Admin@123",
        "Password@123",
        "admin123",
        "admin",
        "Vaibhav@2007",
        "srivaibhav",
        "vaibhav123"
    ]

    print("\n--- PASSLIB VERIFICATION RESULTS ---")
    matched_password = None
    for p in passwords_to_test:
        res = verify_password(p, ADMIN_PASSWORD_HASH)
        print(f"Testing '{p}': {res}")
        if res:
            matched_password = p

    print("\n--- AUTHENTICATE_ADMIN RESULTS ---")
    for p in passwords_to_test:
        res = authenticate_admin("admin@welfare.gov", p)
        print(f"authenticate_admin('admin@welfare.gov', '{p}'): {res}")

    print("\nSUMMARY:")
    if matched_password:
        print(f"SUCCESS: The current hash in .env matches plaintext password: '{matched_password}'")
    else:
        print("WARNING: None of the common test passwords matched the exact hash.")

if __name__ == "__main__":
    check()
