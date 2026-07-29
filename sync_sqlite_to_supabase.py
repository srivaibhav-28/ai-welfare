import os
import sys
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

from app.database import db
from app.supabase_db import supabase_db

def sync_data():
    if not supabase_db.is_configured():
        print("Supabase is not configured.")
        return

    print("--- 1. Syncing Users to Supabase ---")
    users = db.get_users()
    for user in users:
        try:
            res = supabase_db.insert_row("users", user)
            print(f"Synced User: {user.get('email')} -> SUCCESS")
        except Exception as exc:
            print(f"Synced User: {user.get('email')} -> {exc}")

    print("\n--- 2. Syncing Schemes to Supabase ---")
    schemes = db.get_schemes()
    for scheme in schemes:
        try:
            res = supabase_db.insert_row("schemes", scheme)
            print(f"Synced Scheme: {scheme.get('name')} -> SUCCESS")
        except Exception as exc:
            print(f"Synced Scheme: {scheme.get('name')} -> {exc}")

    print("\n--- 3. Syncing Applications to Supabase ---")
    apps = db.get_applications()
    for app_item in apps:
        try:
            res = supabase_db.insert_row("applications", app_item)
            print(f"Synced Application: {app_item.get('id')} -> SUCCESS")
        except Exception as exc:
            print(f"Synced Application: {app_item.get('id')} -> {exc}")

if __name__ == "__main__":
    sync_data()
