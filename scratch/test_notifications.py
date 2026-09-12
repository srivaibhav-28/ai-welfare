import os
import traceback
from fastapi.testclient import TestClient

# Simulate production environment
os.environ["ENVIRONMENT"] = "production"

from run import app
from app.database.supabase_db import db
from app.services.auth_service import create_access_token

client = TestClient(app)

admin_user = db.ensure_single_admin()
admin_token = create_access_token({
    "sub": admin_user["id"],
    "email": admin_user["email"],
    "role": "admin",
    "name": admin_user.get("name", "Admin")
})
headers = {"Authorization": f"Bearer {admin_token}"}

try:
    print("Testing GET /api/admin/notifications in production mode...")
    res = client.get("/api/admin/notifications", headers=headers)
    print("Response Status Code:", res.status_code)
    print("Response Body:", res.text)
except Exception as e:
    print("Caught Exception:", e)
    traceback.print_exc()
