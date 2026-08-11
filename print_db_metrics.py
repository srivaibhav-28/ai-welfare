import os
from app.database.supabase_db import db

def print_metrics():
    print("=" * 80)
    print("DATABASE & SYSTEM METRICS SUMMARY")
    print("=" * 80)

    supabase_url = os.getenv("SUPABASE_URL", "https://mborxydvtiekgnxflsci.supabase.co")
    db_url = os.getenv("DATABASE_URL", "postgresql://postgres:SriVaibhav%402007@db.mborxydvtiekgnxflsci.supabase.co:5432/postgres")

    print(f"1. Database URL / Provider: Supabase Cloud PostgreSQL")
    print(f"   URL: {db_url}")
    print(f"   REST Endpoint: {supabase_url}")

    users = db.get_users()
    schemes = db.get_schemes()
    applications = db.get_applications()

    admins = [u for u in users if u.get("role") == "admin"]
    citizens = [u for u in users if u.get("role") != "admin"]

    print(f"\n2. Connected Database Name: Supabase PostgreSQL (postgres)")
    print(f"\n3. Existing Core Tables:")
    print(f"   - users ({len(users)} rows)")
    print(f"   - schemes ({len(schemes)} rows)")
    print(f"   - applications ({len(applications)} rows)")
    print(f"   - user_documents")
    print(f"   - notifications")
    print(f"   - audit_logs")

    print(f"\n4. Number of Total Users: {len(users)}")
    print(f"5. Number of Admins: {len(admins)}")
    for a in admins:
        print(f"   - Admin ID: {a['id']} | Email: {a['email']} | Role: {a['role']} | Verified: {a.get('is_verified')}")

    print("\n6. Sample Citizen Users:")
    for c in citizens[:3]:
        print(f"   - Citizen ID: {c['id']} | Email: {c['email']} | Name: {c.get('name')} | Verified: {c.get('is_verified')}")

    print("=" * 80)

if __name__ == "__main__":
    print_metrics()
