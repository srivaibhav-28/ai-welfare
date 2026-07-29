import os
import requests
from typing import Dict, Any, Optional
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").strip()
SUPABASE_KEY = (
    os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    or os.environ.get("SUPABASE_ANON_KEY")
    or os.environ.get("SUPABASE_PUBLISHABLE_KEY")
    or ""
).strip()
DATABASE_URL = (
    os.environ.get("DATABASE_URL")
    or os.environ.get("DIRECT_URL", "")
).strip()

class SupabaseManager:
    def __init__(self):
        self.url = os.environ.get("SUPABASE_URL", "").strip()
        self.key = (
            os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
            or os.environ.get("SUPABASE_PUBLISHABLE_KEY")
            or os.environ.get("SUPABASE_ANON_KEY")
            or ""
        ).strip()
        self.is_configured = bool(self.url and self.key)

    def get_headers(self) -> Dict[str, str]:
        return {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }

    # Storage bucket helper
    def upload_file_to_storage(self, bucket: str, file_path_in_bucket: str, file_bytes: bytes, content_type: str = "image/jpeg") -> Optional[str]:
        if not self.is_configured:
            return None
        
        target_url = f"{self.url}/storage/v1/object/{bucket}/{file_path_in_bucket}"
        headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": content_type,
            "x-upsert": "true"
        }
        try:
            res = requests.post(target_url, headers=headers, data=file_bytes)
            if res.status_code in [200, 201]:
                return f"{self.url}/storage/v1/object/public/{bucket}/{file_path_in_bucket}"
            else:
                print(f"[Supabase Storage] Error {res.status_code}: {res.text}")
                return None
        except Exception as e:
            print(f"[Supabase Storage Exception]: {e}")
            return None

    def test_connection(self) -> Dict[str, Any]:
        if not self.is_configured:
            return {"connected": False, "reason": "SUPABASE_URL and a valid Supabase key are not set in environment."}
        try:
            res = requests.get(f"{self.url}/rest/v1/", headers=self.get_headers(), timeout=5)
            if res.status_code in [200, 204]:
                return {"connected": True, "url": self.url, "status": "Online"}
            return {"connected": False, "reason": f"HTTP {res.status_code}: {res.text[:200]}"}
        except Exception as e:
            return {"connected": False, "reason": str(e)}

    # Database REST Operations
    def db_select(self, table: str, select_query: str = "*", params: Optional[Dict[str, str]] = None) -> Optional[Any]:
        if not self.is_configured:
            return None
        url = f"{self.url}/rest/v1/{table}?select={select_query}"
        try:
            res = requests.get(url, headers=self.get_headers(), params=params or {}, timeout=8)
            if res.status_code == 200:
                return res.json()
            return None
        except Exception as e:
            print(f"[Supabase DB Select Error - {table}]: {e}")
            return None

    def db_upsert(self, table: str, data: Dict[str, Any] or List[Dict[str, Any]]) -> Optional[Any]:
        if not self.is_configured:
            return None
        url = f"{self.url}/rest/v1/{table}"
        headers = self.get_headers()
        headers["Resolution"] = "merge-duplicates"
        try:
            res = requests.post(url, headers=headers, json=data, timeout=8)
            if res.status_code in [200, 201]:
                return res.json()
            return None
        except Exception as e:
            print(f"[Supabase DB Upsert Error - {table}]: {e}")
            return None

    def db_delete(self, table: str, column_match: str, value: str) -> bool:
        if not self.is_configured:
            return False
        url = f"{self.url}/rest/v1/{table}?{column_match}=eq.{value}"
        try:
            res = requests.delete(url, headers=self.get_headers(), timeout=8)
            return res.status_code in [200, 204]
        except Exception as e:
            print(f"[Supabase DB Delete Error - {table}]: {e}")
            return False

supabase_client = SupabaseManager()

