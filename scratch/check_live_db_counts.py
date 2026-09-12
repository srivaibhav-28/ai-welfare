import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath("."))

from dotenv import load_dotenv
load_dotenv()

from app.database.supabase_db import db

def check_live():
    print("=" * 80)
    print("        INSPECTING LIVE SUPABASE DATABASE COUNTS                     ")
    print("=" * 80)

    print(f"Supabase Configured: {db.is_supabase_configured}")

    users = db.fetch_rows("users")
    schemes = db.fetch_rows("schemes")
    applications = db.fetch_rows("applications")
    user_documents = db.fetch_rows("user_documents")

    print(f"\n1. Direct Supabase fetch_rows('users'): {len(users)} rows")
    for u in users[:3]:
        print(f"   - User ID: {u.get('id')}, Email: {u.get('email')}, Role: {u.get('role')}")

    print(f"\n2. Direct Supabase fetch_rows('schemes'): {len(schemes)} rows")
    for s in schemes[:3]:
        print(f"   - Scheme ID: {s.get('id')}, Name: {s.get('name')}")

    print(f"\n3. Direct Supabase fetch_rows('applications'): {len(applications)} rows")
    for a in applications[:3]:
        print(f"   - App ID: {a.get('id')}, User: {a.get('user_name')}, Status: {a.get('status')}")

    print(f"\n4. Direct Supabase fetch_rows('user_documents'): {len(user_documents)} rows")

    print(f"\n5. db.get_users(): {len(db.get_users())} users")
    print(f"6. db.get_schemes(): {len(db.get_schemes())} schemes")
    print(f"7. db.get_applications(): {len(db.get_applications())} applications")

if __name__ == "__main__":
    check_live()
