import traceback
from fastapi.testclient import TestClient
from api.applications import app
from app.services.auth_service import require_admin_user

# Test the endpoint directly
client = TestClient(app)

# Override admin auth dependency for testing
app.dependency_overrides[require_admin_user] = lambda: {"id": "admin-1", "email": "admin@welfare.gov", "role": "admin"}

try:
    print("Testing PUT /api/applications/app-123456/status ...")
    res = client.put("/api/applications/app-123456/status", json={"status": "Approved", "remarks": "Test approval"})
    print("Response Status Code:", res.status_code)
    print("Response JSON:", res.json())
except Exception as e:
    print("Caught Exception:", e)
    traceback.print_exc()
