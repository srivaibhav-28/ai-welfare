import os
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").strip()
SUPABASE_KEY = (
    os.environ.get("SUPABASE_PUBLISHABLE_KEY")
    or os.environ.get("SUPABASE_ANON_KEY")
    or os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
).strip()


class SupabaseDB:
    @property
    def url(self) -> str:
        return os.environ.get("SUPABASE_URL", "").strip()

    @property
    def key(self) -> str:
        return (
            os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
            or os.environ.get("SUPABASE_PUBLISHABLE_KEY")
            or os.environ.get("SUPABASE_ANON_KEY")
            or ""
        ).strip()

    @property
    def headers(self) -> Dict[str, str]:
        return {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }

    def is_configured(self) -> bool:
        return bool(self.url and self.key)

    def _build_query(self, filters: Optional[Dict[str, Any]] = None) -> str:
        if not filters:
            return ""
        parts = []
        for key, value in filters.items():
            parts.append(f"{key}=eq.{value}")
        return "&".join(parts)

    def _request(
        self,
        method: str,
        table: str,
        *,
        json_body: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, str]] = None,
        filters: Optional[Dict[str, Any]] = None,
    ):
        if not self.is_configured():
            raise RuntimeError("Supabase credentials are not configured")

        base_url = f"{self.url}/rest/v1/{table}"
        query = self._build_query(filters)
        url = f"{base_url}?{query}" if query else base_url
        try:
            if method == "GET":
                return requests.get(url, headers=self.headers, params=params or {}, timeout=10)
            if method == "POST":
                return requests.post(base_url, headers=self.headers, json=json_body, timeout=10)
            if method == "PATCH":
                return requests.patch(url, headers=self.headers, json=json_body, timeout=10)
            if method == "DELETE":
                return requests.delete(url, headers=self.headers, timeout=10)
        except Exception as exc:
            raise RuntimeError(f"Supabase request failed: {exc}") from exc
        raise ValueError(f"Unsupported method: {method}")

    def fetch_rows(self, table: str, *, filters: Optional[Dict[str, Any]] = None, select: str = "*") -> List[Dict[str, Any]]:
        resp = self._request("GET", table, params={"select": select}, filters=filters)
        if resp.status_code == 200:
            return resp.json()
        raise RuntimeError(resp.text)

    def insert_row(self, table: str, data: Dict[str, Any]) -> Dict[str, Any]:
        resp = self._request("POST", table, json_body=data)
        if resp.status_code in (200, 201):
            payload = resp.json()
            return payload[0] if isinstance(payload, list) and payload else data
        raise RuntimeError(resp.text)

    def update_row(self, table: str, filters: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        resp = self._request("PATCH", table, filters=filters, json_body=data)
        if resp.status_code in (200, 201, 204):
            payload = resp.json() if resp.content else []
            return payload[0] if isinstance(payload, list) and payload else data
        raise RuntimeError(resp.text)

    def delete_rows(self, table: str, filters: Dict[str, Any]) -> bool:
        resp = self._request("DELETE", table, filters=filters)
        return resp.status_code in (200, 204)


supabase_db = SupabaseDB()
