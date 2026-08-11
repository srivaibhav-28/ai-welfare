import os
import sys
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def audit_database():
    print("=" * 80)
    print("DATABASE & SYSTEM COMPREHENSIVE AUDIT")
    print("=" * 80)

    db_url = os.getenv("DATABASE_URL")
    print(f"1. Connection String (DATABASE_URL): {db_url}")

    if not db_url:
        print("   DATABASE_URL not set in environment.")
        return

    try:
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        print("   Database connection successful! ✅")

        # Database Name
        cursor.execute("SELECT current_database();")
        db_name = cursor.fetchone()[0]
        print(f"2. Connected Database Name: {db_name}")

        # Tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name;
        """)
        tables = [row[0] for row in cursor.fetchall()]
        print(f"3. Existing Tables in 'public' schema: {tables}")

        # Users Count
        user_count = 0
        if 'users' in tables:
            cursor.execute("SELECT COUNT(*) FROM users;")
            user_count = cursor.fetchone()[0]
        print(f"4. Total Users in DB: {user_count}")

        # Admins Count
        admin_count = 0
        if 'users' in tables:
            cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin';")
            admin_count = cursor.fetchone()[0]

            cursor.execute("SELECT id, email, role, is_verified FROM users WHERE role = 'admin';")
            admins = cursor.fetchall()
            print(f"5. Number of Admins in 'users' table: {admin_count}")
            for a in admins:
                print(f"   - Admin ID: {a[0]} | Email: {a[1]} | Role: {a[2]} | Verified: {a[3]}")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"   Database audit error: {e}")

if __name__ == "__main__":
    audit_database()
