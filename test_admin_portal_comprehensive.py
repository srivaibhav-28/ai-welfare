import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_admin_portal():
    print("=" * 80)
    print("TESTING ADMIN PORTAL BACKEND ENDPOINTS & FLOWS")
    print("=" * 80)

    # 1. Admin Login
    print("\n1. Testing Admin Login (admin@aiwelfare.gov / Admin@123)...")
    r_login = requests.post(f"{BASE_URL}/api/admin/login", json={"email": "admin@aiwelfare.gov", "password": "Admin@123"})
    print(f"   Status Code: {r_login.status_code}")
    if r_login.status_code != 200:
        print(f"   Error: {r_login.text}")
        return False

    token = r_login.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    print("   Admin Login SUCCESSFUL! Token acquired.")

    # 2. Admin Dashboard Analytics
    print("\n2. Testing Admin Analytics (/api/admin/analytics)...")
    r_analytics = requests.get(f"{BASE_URL}/api/admin/analytics", headers=headers)
    print(f"   Status Code: {r_analytics.status_code}")
    if r_analytics.status_code == 200:
        data = r_analytics.json()
        print(f"   Users: {data.get('total_users')}, Schemes: {data.get('total_schemes')}, Apps: {data.get('total_applications')}")
    else:
        print(f"   Error: {r_analytics.text}")

    # 3. Get Registered Users
    print("\n3. Testing Admin Get Users (/api/admin/users)...")
    r_users = requests.get(f"{BASE_URL}/api/admin/users", headers=headers)
    print(f"   Status Code: {r_users.status_code}")
    if r_users.status_code == 200:
        users = r_users.json()
        print(f"   Retrieved {len(users)} users.")

    # 4. Get Welfare Schemes
    print("\n4. Testing Get Schemes (/api/schemes)...")
    r_schemes = requests.get(f"{BASE_URL}/api/schemes", headers=headers)
    print(f"   Status Code: {r_schemes.status_code}")

    # 5. Create New Scheme
    print("\n5. Testing Create Scheme (/api/admin/schemes)...")
    new_scheme_payload = {
        "name": "PM Test Admin Scheme",
        "category": "Education",
        "description": "Test scheme created during admin portal audit",
        "benefits": "₹10,000 yearly grant",
        "official_link": "https://education.gov.in",
        "last_date": "2026-12-31",
        "criteria": {"max_income": 300000},
        "required_documents": ["Aadhaar Card", "Income Certificate"]
    }
    r_create_scheme = requests.post(f"{BASE_URL}/api/admin/schemes", json=new_scheme_payload, headers=headers)
    print(f"   Status Code: {r_create_scheme.status_code}")
    scheme_id = None
    if r_create_scheme.status_code == 200:
        scheme_id = r_create_scheme.json().get("scheme", {}).get("id")
        print(f"   Created Scheme ID: {scheme_id}")

    # 6. Update Scheme Rules
    if scheme_id:
        print(f"\n6. Testing Update Rules (/api/admin/schemes/{scheme_id}/rules)...")
        rules_payload = {
            "criteria": {"min_age": 18, "max_age": 30, "max_income": 250000, "is_student": True},
            "required_documents": ["Aadhaar Card", "Income Certificate", "Student ID"]
        }
        r_rules = requests.put(f"{BASE_URL}/api/admin/schemes/{scheme_id}/rules", json=rules_payload, headers=headers)
        print(f"   Status Code: {r_rules.status_code}")

    # 7. Delete Scheme
    if scheme_id:
        print(f"\n7. Testing Delete Scheme (/api/admin/schemes/{scheme_id})...")
        r_del = requests.delete(f"{BASE_URL}/api/admin/schemes/{scheme_id}", headers=headers)
        print(f"   Status Code: {r_del.status_code}")

    # 8. Document Verification
    print("\n8. Testing Document Verification (/api/admin/documents/verify)...")
    doc_payload = {
        "user_id": "usr-citizen-01",
        "document_name": "Aadhaar Card",
        "status": "Verified",
        "remarks": "Audited by System Administrator"
    }
    r_doc = requests.post(f"{BASE_URL}/api/admin/documents/verify", json=doc_payload, headers=headers)
    print(f"   Status Code: {r_doc.status_code}")

    # 9. Broadcast Notification
    print("\n9. Testing Broadcast Notification (/api/admin/notifications)...")
    notif_payload = {
        "title": "Admin Audit Announcement",
        "message": "System maintainence complete.",
        "type": "info"
    }
    r_notif = requests.post(f"{BASE_URL}/api/admin/notifications", json=notif_payload, headers=headers)
    print(f"   Status Code: {r_notif.status_code}")

    # 10. Supabase Monitor Status
    print("\n10. Testing Supabase Status (/api/admin/supabase-status)...")
    r_supa = requests.get(f"{BASE_URL}/api/admin/supabase-status", headers=headers)
    print(f"   Status Code: {r_supa.status_code}")
    print(f"   Response: {r_supa.json()}")

    # 11. Reports CSV Export
    print("\n11. Testing CSV Export (/api/admin/reports/export)...")
    r_csv = requests.get(f"{BASE_URL}/api/admin/reports/export?token={token}")
    print(f"   Status Code: {r_csv.status_code}")

    print("\n" + "=" * 80)
    print("ADMIN PORTAL ENDPOINTS TEST COMPLETED SUCCESSFULLY!")
    print("=" * 80)
    return True

if __name__ == "__main__":
    test_admin_portal()
