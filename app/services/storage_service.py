import os
import requests
from typing import Optional, Dict, Any
from app.config import config

class StorageService:
    @staticmethod
    def upload_file_to_supabase(
        bucket: str,
        file_path_in_bucket: str,
        file_bytes: bytes,
        content_type: str = "image/jpeg"
    ) -> Optional[str]:
        if not config.SUPABASE_URL or not config.SUPABASE_SERVICE_ROLE_KEY or not config.ENABLE_SUPABASE_STORAGE:
            return None
        
        target_url = f"{config.SUPABASE_URL}/storage/v1/object/{bucket}/{file_path_in_bucket}"
        headers = {
            "apikey": config.SUPABASE_SERVICE_ROLE_KEY or config.SUPABASE_ANON_KEY,
            "Authorization": f"Bearer {config.SUPABASE_SERVICE_ROLE_KEY or config.SUPABASE_ANON_KEY}",
            "Content-Type": content_type,
            "x-upsert": "true"
        }
        try:
            res = requests.post(target_url, headers=headers, data=file_bytes, timeout=5)
            if res.status_code in [200, 201]:
                return f"{config.SUPABASE_URL}/storage/v1/object/public/{bucket}/{file_path_in_bucket}"
            else:
                print(f"[Supabase Storage] Error {res.status_code}: {res.text}")
                return None
        except Exception as e:
            print(f"[Supabase Storage Exception]: {e}")
            return None

    @staticmethod
    def test_connection() -> Dict[str, Any]:
        if not config.SUPABASE_URL or not (config.SUPABASE_SERVICE_ROLE_KEY or config.SUPABASE_ANON_KEY):
            return {"connected": False, "reason": "SUPABASE_URL and Supabase Keys are not set in environment."}
        headers = {
            "apikey": config.SUPABASE_SERVICE_ROLE_KEY or config.SUPABASE_ANON_KEY,
            "Authorization": f"Bearer {config.SUPABASE_SERVICE_ROLE_KEY or config.SUPABASE_ANON_KEY}",
            "Content-Type": "application/json"
        }
        try:
            res = requests.get(f"{config.SUPABASE_URL}/rest/v1/", headers=headers, timeout=5)
            if res.status_code in [200, 204]:
                return {"connected": True, "url": config.SUPABASE_URL, "status": "Online"}
            return {"connected": False, "reason": f"HTTP {res.status_code}: {res.text[:200]}"}
        except Exception as e:
            return {"connected": False, "reason": str(e)}

storage_service = StorageService()
