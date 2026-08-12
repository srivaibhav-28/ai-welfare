import os
import json
import uuid
import datetime
import traceback
from typing import Dict, List, Any, Optional
import requests
from app.config import config

INITIAL_SCHEMES = [
    {
        "id": "scheme-001",
        "name": "PM-Kisan Samman Nidhi (PM-KISAN)",
        "category": "Agriculture",
        "description": "Financial benefit of ₹6,000 per year transferred directly into the bank accounts of landholding farmer families across India in 3 equal installments.",
        "benefits": "₹6,000 per annum direct cash transfer in 3 equal installments of ₹2,000.",
        "criteria": {
            "farmer_status": True,
            "max_income": 300000
        },
        "required_documents": [
            "Aadhaar Card",
            "Land Ownership Document (Khatauni/Khasra)",
            "Active Bank Passbook",
            "Residence Certificate"
        ],
        "official_link": "https://pmkisan.gov.in",
        "last_date": "Open Round the Year",
        "state_restriction": "All",
        "icon": "sprout"
    },
    {
        "id": "scheme-002",
        "name": "Ayushman Bharat PM Jan Arogya Yojana (PM-JAY)",
        "category": "Healthcare",
        "description": "World's largest government-funded health insurance scheme offering cashless coverage up to ₹5 Lakh per family per year for hospitalization.",
        "benefits": "Cashless & paperless health insurance cover up to ₹5,000,000 per family per year for secondary and tertiary care hospitalization.",
        "criteria": {
            "bpl_status": True,
            "max_income": 250000
        },
        "required_documents": [
            "Aadhaar Card",
            "Ration Card / BPL Card",
            "Income Certificate",
            "Residence Certificate"
        ],
        "official_link": "https://pmjay.gov.in",
        "last_date": "Ongoing Scheme",
        "state_restriction": "All",
        "icon": "activity"
    },
    {
        "id": "scheme-003",
        "name": "Pradhan Mantri Awas Yojana (PMAY)",
        "category": "Housing",
        "description": "Provides financial subsidy and financial assistance to construct a pucca house with toilet, electricity, and clean cooking water facilities.",
        "benefits": "Financial assistance of ₹1,20,000 to ₹1,30,000 for house construction plus interest subvention up to 6.5%.",
        "criteria": {
            "max_income": 300000,
            "bpl_status": True
        },
        "required_documents": [
            "Aadhaar Card",
            "Income Certificate",
            "Bank Passbook",
            "Land / Property Rights Document",
            "Passport-size Photograph"
        ],
        "official_link": "https://pmaymis.gov.in",
        "last_date": "31-12-2026",
        "state_restriction": "All",
        "icon": "home"
    },
    {
        "id": "scheme-004",
        "name": "National Scholarship Portal (NSP) Post-Matric Scholarship",
        "category": "Education",
        "description": "Financial grant for students belonging to SC, ST, OBC, EWS, or economically weaker families pursuing post-secondary or higher education.",
        "benefits": "Up to ₹25,000 annual fee reimbursement, maintenance allowance, and academic book grants.",
        "criteria": {
            "student_status": True,
            "max_income": 250000
        },
        "required_documents": [
            "Aadhaar Card",
            "Income Certificate",
            "Caste Certificate",
            "Marksheet of Last Examination",
            "Student ID / Bonafide Certificate",
            "Bank Passbook"
        ],
        "official_link": "https://scholarships.gov.in",
        "last_date": "31-10-2026",
        "state_restriction": "All",
        "icon": "graduation-cap"
    },
    {
        "id": "scheme-005",
        "name": "Indira Gandhi National Old Age Pension Scheme (IGNOAPS)",
        "category": "Pension",
        "description": "Social security pension scheme delivering monthly financial assistance directly into the bank accounts of senior citizens in low-income families.",
        "benefits": "Monthly pension of ₹500 to ₹1,000 directly transferred to eligible senior citizens.",
        "criteria": {
            "min_age": 60,
            "bpl_status": True
        },
        "required_documents": [
            "Aadhaar Card",
            "Age Proof Certificate / Voter ID",
            "BPL Ration Card",
            "Bank Passbook",
            "Residence Certificate"
        ],
        "official_link": "https://nsap.nic.in",
        "last_date": "Open Round the Year",
        "state_restriction": "All",
        "icon": "user-check"
    },
    {
        "id": "scheme-006",
        "name": "Sukanya Samriddhi Yojana (SSY)",
        "category": "Women & Child",
        "description": "Government-backed savings scheme aimed at securing the financial future, higher education, and marriage expense of girl children.",
        "benefits": "High guaranteed tax-free interest (8.2% p.a.), tax savings under 80C, and lump sum maturity corpus.",
        "criteria": {
            "gender": "Female",
            "max_age": 25
        },
        "required_documents": [
            "Birth Certificate of Girl Child",
            "Guardian's Aadhaar Card",
            "Residence Certificate",
            "Passport Photographs",
            "Bank Passbook"
        ],
        "official_link": "https://www.indiapost.gov.in",
        "last_date": "Open Scheme",
        "state_restriction": "All",
        "icon": "heart"
    },
    {
        "id": "scheme-007",
        "name": "PM Garib Kalyan Anna Yojana (PMGKAY)",
        "category": "Food Security",
        "description": "National food security welfare scheme providing free food grains per month to eligible priority households and BPL cardholders.",
        "benefits": "5 KG free wheat/rice per family member every month through National Food Security Act (NFSA).",
        "criteria": {
            "bpl_status": True
        },
        "required_documents": [
            "Aadhaar Card",
            "BPL / Ration Card",
            "Residence Certificate"
        ],
        "official_link": "https://nfsa.gov.in",
        "last_date": "Ongoing Scheme",
        "state_restriction": "All",
        "icon": "shopping-bag"
    },
    {
        "id": "scheme-008",
        "name": "Indira Gandhi National Widow Pension Scheme (IGNWPS)",
        "category": "Pension",
        "description": "Financial protection scheme providing monthly income support for widowed women from underprivileged backgrounds.",
        "benefits": "Monthly pension of ₹600 to ₹1,200 deposited directly into savings accounts.",
        "criteria": {
            "widow_status": True,
            "min_age": 40,
            "bpl_status": True
        },
        "required_documents": [
            "Aadhaar Card",
            "Death Certificate of Husband",
            "Income Certificate",
            "BPL Ration Card",
            "Bank Passbook"
        ],
        "official_link": "https://nsap.nic.in",
        "last_date": "Open Scheme",
        "state_restriction": "All",
        "icon": "shield"
    },
    {
        "id": "scheme-009",
        "name": "Divyangjan Disability Financial Pension Assistance",
        "category": "Disability Assistance",
        "description": "Monthly disability pension and assistive device grant provided to persons with benchmark disabilities to promote financial independence.",
        "benefits": "Monthly allowance of ₹1,000 to ₹1,500 plus free allocation of motorized tricycles, hearing aids, or prosthetic devices.",
        "criteria": {
            "disability_status": True,
            "max_income": 200000
        },
        "required_documents": [
            "Aadhaar Card",
            "Disability Certificate (40%+ certified by Medical Board)",
            "Income Certificate",
            "Bank Passbook",
            "Passport Photo"
        ],
        "official_link": "https://disabilityaffairs.gov.in",
        "last_date": "Open Scheme",
        "state_restriction": "All",
        "icon": "heart-pulse"
    },
    {
        "id": "scheme-010",
        "name": "PM SVANidhi Micro-Credit Scheme",
        "category": "Employment",
        "description": "Special micro-credit facility empowering street vendors, micro-entrepreneurs, and small business owners with collateral-free working capital loans.",
        "benefits": "Collateral-free working capital loan of ₹10,000 to ₹50,000 with 7% interest rate subsidy and digital transaction cashback.",
        "criteria": {
            "occupation_in": ["Street Vendor", "Vendor", "Self-Employed", "Daily Wager", "Laborer", "Business"],
            "max_income": 300000
        },
        "required_documents": [
            "Aadhaar Card",
            "Certificate of Vending / Urban Local Body ID",
            "Bank Passbook",
            "Passport Photograph"
        ],
        "official_link": "https://pmsvanidhi.mohua.gov.in",
        "last_date": "31-12-2026",
        "state_restriction": "All",
        "icon": "briefcase"
    }
]

INITIAL_USERS = [
    {
        "id": "usr-admin-01",
        "email": "admin@aiwelfare.gov",
        "password_hash": "Admin@123",
        "name": "System Administrator",
        "role": "admin",
        "is_verified": True,
        "profile": {}
    },
    {
        "id": "usr-admin-02",
        "email": "admin@welfare.gov",
        "password_hash": "admin123",
        "name": "System Administrator",
        "role": "admin",
        "is_verified": True,
        "profile": {}
    },
    {
        "id": "usr-citizen-01",
        "email": "citizen@welfare.gov",
        "password_hash": "password123",
        "name": "Rajesh Kumar",
        "role": "citizen",
        "is_verified": True,
        "profile": {
            "name": "Rajesh Kumar",
            "age": 42,
            "gender": "Male",
            "state": "Uttar Pradesh",
            "district": "Varanasi",
            "occupation": "Farmer",
            "annual_income": 120000,
            "education": "Secondary",
            "caste_category": "OBC",
            "disability_status": False,
            "student_status": False,
            "farmer_status": True,
            "senior_citizen_status": False,
            "widow_status": False,
            "bpl_status": True
        }
    }
]

class SupabaseDatabase:
    def __init__(self):
        self._in_memory_users = list(INITIAL_USERS)
        self._in_memory_schemes = list(INITIAL_SCHEMES)
        self._in_memory_applications = []
        self._in_memory_documents = {}
        self._in_memory_notifications = [
            {
                "id": "notif-001",
                "title": "Welcome to Welfare Portal",
                "message": "Complete your profile to discover eligible government schemes instantly.",
                "target_user_id": None,
                "type": "info",
                "created_at": "2026-03-01T10:00:00"
            },
            {
                "id": "notif-002",
                "title": "Document Requirement Notice",
                "message": "Please ensure all uploaded documents are strictly in JPEG (.jpg / .jpeg) format.",
                "target_user_id": None,
                "type": "warning",
                "created_at": "2026-03-10T12:30:00"
            }
        ]

    @property
    def is_production(self) -> bool:
        env = (os.environ.get("ENVIRONMENT") or os.environ.get("VERCEL_ENV") or "").lower()
        return bool(os.environ.get("VERCEL") == "1" or env in ["production", "prod", "preview"])

    @property
    def is_supabase_configured(self) -> bool:
        return bool(config.SUPABASE_URL and config.SUPABASE_SERVICE_ROLE_KEY)

    def _headers(self) -> Dict[str, str]:
        return {
            "apikey": config.SUPABASE_SERVICE_ROLE_KEY or config.SUPABASE_ANON_KEY,
            "Authorization": f"Bearer {config.SUPABASE_SERVICE_ROLE_KEY or config.SUPABASE_ANON_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }

    # REST helper methods
    def fetch_rows(self, table: str, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        print("\n========== SUPABASE RUNTIME DIAGNOSTICS ==========")
        print("SUPABASE_URL exists:", bool(config.SUPABASE_URL))
        print("SUPABASE_SERVICE_ROLE_KEY exists:", bool(config.SUPABASE_SERVICE_ROLE_KEY))
        print("SUPABASE_SERVICE_ROLE_KEY length:", len(config.SUPABASE_SERVICE_ROLE_KEY or ""))
        print("SUPABASE_ANON_KEY exists:", bool(config.SUPABASE_ANON_KEY))
        print("SUPABASE_ANON_KEY length:", len(config.SUPABASE_ANON_KEY or ""))
        print("is_supabase_configured:", self.is_supabase_configured)
        print("is_production:", self.is_production)
        print("table:", table)
        print("filters:", filters)

        if not self.is_supabase_configured:
            if self.is_production:
                err_msg = "Production Database Error: SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY is missing in Vercel environment."
                print(f"[PRODUCTION ERROR] {err_msg}")
                raise RuntimeError(err_msg)
            print("USING IN-MEMORY DATABASE")
            return self.fetch_rows_in_memory(table, filters)

        url = f"{config.SUPABASE_URL}/rest/v1/{table}?select=*"
        if filters:
            for k, v in filters.items():
                url += f"&{k}=eq.{v}"

        print("USING SUPABASE REST")
        print("REQUEST URL:", url)

        try:
            res = requests.get(url, headers=self._headers(), timeout=5)
            print("STATUS:", res.status_code)
            print("BODY:", res.text[:500])
            if res.status_code == 200:
                return res.json()
            
            err_msg = f"Supabase REST API Error (Status {res.status_code}): {res.text[:500]}"
            if self.is_production:
                print(f"[PRODUCTION REST ERROR] {err_msg}")
                raise RuntimeError(err_msg)
        except Exception as e:
            if isinstance(e, RuntimeError):
                raise
            err_msg = f"Supabase Request Exception ({type(e).__name__}): {str(e)}"
            print(f"[PRODUCTION EXCEPTION ERROR] {err_msg}")
            if self.is_production:
                raise RuntimeError(err_msg) from e

        print("USING IN-MEMORY DATABASE (POST-FETCH FALLBACK)")
        print("=================================================\n")
        return self.fetch_rows_in_memory(table, filters)

    def fetch_rows_in_memory(self, table: str, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        if table == "users":
            if filters:
                res = list(self._in_memory_users)
                for k, v in filters.items():
                    res = [u for u in res if str(u.get(k, "")).lower() == str(v).lower()]
                return res
            return self._in_memory_users
        elif table == "schemes":
            return self._in_memory_schemes
        elif table == "applications":
            if filters and "user_id" in filters:
                return [a for a in self._in_memory_applications if a.get("user_id") == filters["user_id"]]
            return self._in_memory_applications
        return []

    def insert_row(self, table: str, data: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{config.SUPABASE_URL}/rest/v1/{table}" if config.SUPABASE_URL else ""
        print("\n========== SUPABASE INSERT DIAGNOSTICS ==========")
        print("TABLE:", table)
        print("DATA:", json.dumps(data, indent=2) if isinstance(data, dict) else data)
        print("SUPABASE_URL present:", bool(config.SUPABASE_URL))
        print("SUPABASE_SERVICE_ROLE_KEY present:", bool(config.SUPABASE_SERVICE_ROLE_KEY))
        print("Request URL:", url)

        if self.is_supabase_configured:
            try:
                res = requests.post(url, headers=self._headers(), json=data, timeout=5)
                print("HTTP Status:", res.status_code)
                print("Response Body:", res.text[:1000])
                if res.status_code in [200, 201]:
                    res_json = res.json()
                    return res_json[0] if isinstance(res_json, list) and res_json else data

                raise RuntimeError(
                    f"Supabase INSERT failed: {res.status_code} - {res.text}"
                )
            except Exception:
                print(traceback.format_exc())
                raise

        if self.is_production:
            raise RuntimeError("Supabase is not configured in production environment.")

        # Update in-memory fallback (local development only)
        if table == "users":
            self._in_memory_users.append(data)
        elif table == "schemes":
            self._in_memory_schemes.append(data)
        elif table == "applications":
            self._in_memory_applications.append(data)
        elif table == "notifications":
            self._in_memory_notifications.insert(0, data)
        return data

    def update_row(self, table: str, filters: Dict[str, Any], data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if self.is_supabase_configured:
            query = "&".join([f"{k}=eq.{v}" for k, v in filters.items()])
            url = f"{config.SUPABASE_URL}/rest/v1/{table}?{query}"
            try:
                res = requests.patch(url, headers=self._headers(), json=data, timeout=5)
                if res.status_code in [200, 201, 204]:
                    res_json = res.json() if res.content else []
                    return res_json[0] if isinstance(res_json, list) and res_json else data
            except Exception as e:
                print(f"[Supabase DB Update Error - {table}]: {e}")

        # In-memory update
        if table == "users" and "id" in filters:
            for u in self._in_memory_users:
                if u["id"] == filters["id"]:
                    u.update(data)
                    return u
        elif table == "schemes" and "id" in filters:
            for s in self._in_memory_schemes:
                if s["id"] == filters["id"]:
                    s.update(data)
                    return s
        elif table == "applications" and "id" in filters:
            for a in self._in_memory_applications:
                if a["id"] == filters["id"]:
                    a.update(data)
                    return a
        return data

    def delete_rows(self, table: str, filters: Dict[str, Any]) -> bool:
        if self.is_supabase_configured:
            query = "&".join([f"{k}=eq.{v}" for k, v in filters.items()])
            url = f"{config.SUPABASE_URL}/rest/v1/{table}?{query}"
            try:
                res = requests.delete(url, headers=self._headers(), timeout=5)
                if res.status_code in [200, 204]:
                    return True
            except Exception as e:
                print(f"[Supabase DB Delete Error - {table}]: {e}")

        # In-memory delete
        if table == "users" and "id" in filters:
            self._in_memory_users = [u for u in self._in_memory_users if u.get("id") != filters["id"]]
        elif table == "schemes" and "id" in filters:
            self._in_memory_schemes = [s for s in self._in_memory_schemes if s.get("id") != filters["id"]]
        return True

    # High level domain operations
    def get_users(self) -> List[Dict[str, Any]]:
        users = self.fetch_rows("users")
        if not users and not self.is_production:
            users = self._in_memory_users
        return users or []

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        rows = self.fetch_rows("users", {"email": email.strip().lower()})
        if rows:
            u = rows[0]
            if email.lower() == "admin@welfare.gov" and not u.get("password_hash"):
                u["password_hash"] = "admin123"
            return u
        if not self.is_production:
            for u in self._in_memory_users:
                if u.get("email", "").lower() == email.lower():
                    return u
        return None

    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        rows = self.fetch_rows("users", {"id": user_id})
        if rows:
            return rows[0]
        if not self.is_production:
            for u in self._in_memory_users:
                if u.get("id") == user_id:
                    return u
        return None

    def add_user(self, user: Dict[str, Any]):
        return self.insert_row("users", user)

    def update_user_profile(self, user_id: str, profile: Dict[str, Any]):
        return self.update_row("users", {"id": user_id}, {"profile": profile})

    def update_user_password(self, user_id: str, new_password_hash: str) -> bool:
        res = self.update_row("users", {"id": user_id}, {"password_hash": new_password_hash})
        return res is not None

    def update_user_status(self, user_id: str, is_blocked: bool) -> Optional[Dict[str, Any]]:
        return self.update_row("users", {"id": user_id}, {"is_blocked": is_blocked})

    def verify_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        from datetime import datetime, timezone
        now_iso = datetime.now(timezone.utc).isoformat()
        return self.update_row("users", {"id": user_id}, {"is_verified": True, "verified_at": now_iso})

    def delete_user(self, user_id: str) -> bool:
        self.delete_rows("users", {"id": user_id})
        self.delete_rows("user_documents", {"user_id": user_id})
        self.delete_rows("applications", {"user_id": user_id})
        return True

    def get_schemes(self) -> List[Dict[str, Any]]:
        schemes = self.fetch_rows("schemes")
        if not schemes:
            schemes = self._in_memory_schemes
        return schemes

    def get_scheme_by_id(self, scheme_id: str) -> Optional[Dict[str, Any]]:
        schemes = self.get_schemes()
        for s in schemes:
            if s.get("id") == scheme_id:
                return s
        return None

    def add_scheme(self, scheme: Dict[str, Any]):
        return self.insert_row("schemes", scheme)

    def update_scheme(self, scheme_id: str, updated_data: Dict[str, Any]):
        return self.update_row("schemes", {"id": scheme_id}, updated_data)

    def delete_scheme(self, scheme_id: str) -> bool:
        return self.delete_rows("schemes", {"id": scheme_id})

    def get_applications(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        filters = {"user_id": user_id} if user_id else None
        apps = self.fetch_rows("applications", filters)
        return apps

    def add_application(self, app_data: Dict[str, Any]):
        return self.insert_row("applications", app_data)

    def update_application_status(self, app_id: str, status: str, remarks: str = ""):
        return self.update_row("applications", {"id": app_id}, {"status": status, "remarks": remarks})

    def get_user_documents(self, user_id: str) -> Dict[str, Any]:
        rows = self.fetch_rows("user_documents", {"user_id": user_id})
        docs_map = {}
        for r in rows:
            doc_name = r.get("document_name")
            if doc_name:
                docs_map[doc_name] = {
                    "status": r.get("status"),
                    "upload_date": r.get("upload_date"),
                    "file_name": r.get("file_name"),
                    "file_url": r.get("file_url"),
                    "remarks": r.get("remarks"),
                    "verified_by": r.get("verified_by")
                }
        if not docs_map and user_id in self._in_memory_documents:
            docs_map = self._in_memory_documents[user_id]
        return docs_map

    def update_user_document(self, user_id: str, doc_name: str, doc_info: Dict[str, Any]):
        if user_id not in self._in_memory_documents:
            self._in_memory_documents[user_id] = {}
        self._in_memory_documents[user_id][doc_name] = doc_info

        payload = {
            "user_id": user_id,
            "document_name": doc_name,
            "status": doc_info.get("status", "Uploaded"),
            "upload_date": doc_info.get("upload_date"),
            "file_name": doc_info.get("file_name"),
            "file_url": doc_info.get("file_url"),
            "remarks": doc_info.get("remarks"),
            "verified_by": doc_info.get("verified_by")
        }
        if self.is_supabase_configured:
            try:
                # Try patch first
                res = self.update_row("user_documents", {"user_id": user_id, "document_name": doc_name}, payload)
                if not res:
                    self.insert_row("user_documents", payload)
            except Exception:
                pass
        return doc_info

    def get_notifications(self, target_user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        notifs = self.fetch_rows("notifications")
        if not notifs:
            notifs = self._in_memory_notifications
        if target_user_id:
            return [n for n in notifs if n.get("target_user_id") is None or n.get("target_user_id") == target_user_id]
        return notifs

    def add_notification(self, notif_data: Dict[str, Any]):
        return self.insert_row("notifications", notif_data)

    def get_audit_logs(self) -> List[Dict[str, Any]]:
        logs = self.fetch_rows("audit_logs")
        if not logs:
            logs = getattr(self, "_in_memory_audit_logs", [])
        return logs

    def add_audit_log(self, action: str, performed_by: str, details: str = "", ip_address: str = "127.0.0.1"):
        log_entry = {
            "id": f"log-{uuid.uuid4().hex[:6]}",
            "action": action,
            "performed_by": performed_by,
            "details": details,
            "ip_address": ip_address,
            "created_at": datetime.datetime.now().isoformat()
        }
        if not hasattr(self, "_in_memory_audit_logs"):
            self._in_memory_audit_logs = []
        self._in_memory_audit_logs.insert(0, log_entry)
        if self.is_supabase_configured:
            try:
                self.insert_row("audit_logs", log_entry)
            except Exception:
                pass
        return log_entry

db = SupabaseDatabase()
