import os
import sys
import uuid
import datetime

# Ensure project root is in path
sys.path.insert(0, os.path.abspath("."))

from fastapi.testclient import TestClient
from api.applications import app
from app.database.supabase_db import db
from app.services.auth_service import create_access_token

client = TestClient(app)

def test_admin_payment_rendering_flow():
    print("=== VERIFYING ADMIN PAYMENT MANAGEMENT FLOW ===")

    # 1. Check existing payment rows in Supabase / DB
    existing_payments = db.get_payments()
    n_count = len(existing_payments)
    print(f"[STEP 1 - SUPABASE DB] Currently contains {n_count} payment rows in database table.")

    # 2. Call GET /api/payments using admin token
    admin_token = create_access_token({
        "sub": "usr-admin-aadc2d",
        "email": "admin@welfare.gov",
        "role": "admin",
        "id": "usr-admin-aadc2d"
    })
    headers = {"Authorization": f"Bearer {admin_token}"}

    response = client.get("/api/payments", headers=headers)
    print(f"[STEP 2 - BACKEND API] GET /api/payments status code: {response.status_code}")
    assert response.status_code == 200, f"API failed: {response.text}"
    
    data = response.json()
    assert data.get("status") == "success"
    payments = data.get("payments", [])
    analytics = data.get("analytics", {})
    
    print(f"[STEP 2 - BACKEND API] Returned count: {len(payments)}, Analytics: {analytics}")
    assert len(payments) == n_count, f"API returned {len(payments)} rows, expected {n_count}"

    # 3. Verify HTML DOM elements in index.html match JS targets
    with open("index.html", "r", encoding="utf-8") as f:
        html_content = f.read()

    assert 'id="adminPaymentsTableBody"' in html_content, "Missing adminPaymentsTableBody in index.html"
    assert 'id="payStatTotal"' in html_content, "Missing payStatTotal in index.html"
    assert 'id="adminPaySearch"' in html_content, "Missing adminPaySearch in index.html"
    assert 'id="adminPayFilterStatus"' in html_content, "Missing adminPayFilterStatus in index.html"

    print("[STEP 3 - UI CONTRACT] index.html table body ID 'adminPaymentsTableBody' and stat card IDs verified.")
    print("\n=== ALL 3 STEPS VERIFIED 100% SUCCESS ===")

if __name__ == "__main__":
    test_admin_payment_rendering_flow()
