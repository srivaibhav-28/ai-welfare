import os
import requests
from typing import Dict, Any, Optional

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.environ.get("SUPABASE_ANON_KEY", os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")).strip()

class SupabaseManager:
    def __init__(self):
        self.url = SUPABASE_URL
        self.key = SUPABASE_KEY
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
                # Public URL format
                return f"{self.url}/storage/v1/object/public/{bucket}/{file_path_in_bucket}"
            else:
                print(f"[Supabase Storage] Error {res.status_code}: {res.text}")
                return None
        except Exception as e:
            print(f"[Supabase Storage Exception]: {e}")
            return None

supabase_client = SupabaseManager()
