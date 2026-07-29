import json
import os
import sqlite3
from typing import Dict, List, Any, Optional
import requests
from dotenv import load_dotenv

from app.supabase_db import supabase_db

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

DB_FILE = os.environ.get("DATA_STORE_FILE") or os.path.join(BASE_DIR, "data_store.json")
SQLITE_FILE = os.environ.get("SQLITE_DB_FILE") or os.path.join(BASE_DIR, "data_store.sqlite3")
USE_SUPABASE = os.environ.get("USE_SUPABASE", "true").lower() == "true"
SUPABASE_URL = os.environ.get("SUPABASE_URL", "").strip()
SUPABASE_KEY = (
    os.environ.get("SUPABASE_PUBLISHABLE_KEY")
    or os.environ.get("SUPABASE_ANON_KEY")
    or os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
).strip()

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
        "email": "admin@welfare.gov",
        "password_hash": "admin123",  # Demo simplified auth
        "name": "System Administrator",
        "role": "admin",
        "profile": {}
    },
    {
        "id": "usr-citizen-01",
        "email": "citizen@welfare.gov",
        "password_hash": "password123",
        "name": "Rajesh Kumar",
        "role": "citizen",
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

class Database:
    def __init__(self, db_file: str = DB_FILE):
        self.db_file = db_file
        self.sqlite_file = SQLITE_FILE
        self.use_supabase = USE_SUPABASE and bool(SUPABASE_URL and SUPABASE_KEY)
        self._initialize_sqlite()
        self.load_data()

    def _initialize_sqlite(self):
        conn = sqlite3.connect(self.sqlite_file)
        try:
            conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                name TEXT NOT NULL,
                mobile_number TEXT,
                role TEXT NOT NULL,
                profile TEXT
            )
            """)
            conn.execute("""
            CREATE TABLE IF NOT EXISTS schemes (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                category TEXT,
                description TEXT,
                benefits TEXT,
                criteria TEXT,
                required_documents TEXT,
                official_link TEXT,
                last_date TEXT,
                state_restriction TEXT,
                icon TEXT
            )
            """)
            conn.execute("""
            CREATE TABLE IF NOT EXISTS applications (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                user_name TEXT,
                user_email TEXT,
                scheme_id TEXT NOT NULL,
                scheme_name TEXT NOT NULL,
                status TEXT NOT NULL,
                applied_date TEXT,
                uploaded_documents TEXT,
                remarks TEXT
            )
            """)
            conn.execute("""
            CREATE TABLE IF NOT EXISTS user_documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                document_name TEXT NOT NULL,
                status TEXT NOT NULL,
                upload_date TEXT,
                file_name TEXT,
                file_url TEXT,
                remarks TEXT,
                verified_by TEXT,
                UNIQUE(user_id, document_name)
            )
            """)
            conn.commit()
        finally:
            conn.close()

    def _load_from_supabase(self) -> Optional[Dict[str, Any]]:
        if not self.use_supabase:
            return None
        try:
            users = supabase_db.fetch_rows("users") if supabase_db.is_configured() else []
            schemes = supabase_db.fetch_rows("schemes") if supabase_db.is_configured() else INITIAL_SCHEMES
            applications = supabase_db.fetch_rows("applications") if supabase_db.is_configured() else []
            user_documents = {}
            for user in users:
                docs = supabase_db.fetch_rows("user_documents", filters={"user_id": user.get("id")}) if supabase_db.is_configured() else []
                docs_map = {}
                for doc in docs:
                    docs_map[doc.get("document_name")] = {
                        "status": doc.get("status"),
                        "upload_date": doc.get("upload_date"),
                        "file_name": doc.get("file_name"),
                        "file_url": doc.get("file_url"),
                        "remarks": doc.get("remarks"),
                        "verified_by": doc.get("verified_by"),
                    }
                if docs_map:
                    user_documents[user.get("id")] = docs_map
            if not users:
                return None
            return {"users": users, "schemes": schemes, "applications": applications, "user_documents": user_documents}
        except Exception as exc:
            print(f"[Supabase] load failed: {exc}")
        return None

    def _sync_sqlite_from_json(self):
        conn = sqlite3.connect(self.sqlite_file)
        try:
            conn.execute("DELETE FROM users")
            conn.execute("DELETE FROM schemes")
            conn.execute("DELETE FROM applications")
            conn.execute("DELETE FROM user_documents")
            for user in self.data.get("users", []):
                if not user.get("id") or not user.get("email"):
                    continue
                conn.execute(
                    "INSERT OR REPLACE INTO users (id, email, password_hash, name, mobile_number, role, profile) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        user.get("id"),
                        user.get("email"),
                        user.get("password_hash") or "",
                        user.get("name") or "User",
                        user.get("mobile_number") or "",
                        user.get("role") or "citizen",
                        json.dumps(user.get("profile", {}) if isinstance(user.get("profile"), dict) else {}),
                    ),
                )
            for scheme in self.data.get("schemes", []):
                if not scheme.get("id"):
                    continue
                conn.execute(
                    "INSERT OR REPLACE INTO schemes (id, name, category, description, benefits, criteria, required_documents, official_link, last_date, state_restriction, icon) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        scheme.get("id"),
                        scheme.get("name") or "Scheme",
                        scheme.get("category") or "General",
                        scheme.get("description") or "",
                        scheme.get("benefits") or "",
                        json.dumps(scheme.get("criteria", {}) if isinstance(scheme.get("criteria"), dict) else {}),
                        json.dumps(scheme.get("required_documents", []) if isinstance(scheme.get("required_documents"), list) else []),
                        scheme.get("official_link") or "",
                        scheme.get("last_date") or "",
                        scheme.get("state_restriction") or "",
                        scheme.get("icon") or "",
                    ),
                )
            for application in self.data.get("applications", []):
                if not application.get("id"):
                    continue
                conn.execute(
                    "INSERT OR REPLACE INTO applications (id, user_id, user_name, user_email, scheme_id, scheme_name, status, applied_date, uploaded_documents, remarks) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        application.get("id"),
                        application.get("user_id") or "",
                        application.get("user_name") or "",
                        application.get("user_email") or "",
                        application.get("scheme_id") or "",
                        application.get("scheme_name") or "",
                        application.get("status") or "Applied",
                        application.get("applied_date") or "",
                        json.dumps(application.get("uploaded_documents", {}) if isinstance(application.get("uploaded_documents"), dict) else {}),
                        application.get("remarks") or "",
                    ),
                )
            for user_id, docs in self.data.get("user_documents", {}).items():
                if isinstance(docs, dict):
                    for doc_name, doc_info in docs.items():
                        if doc_name and isinstance(doc_info, dict):
                            conn.execute(
                                "INSERT OR REPLACE INTO user_documents (user_id, document_name, status, upload_date, file_name, file_url, remarks, verified_by) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                                (
                                    user_id,
                                    doc_name,
                                    doc_info.get("status") or "Uploaded",
                                    doc_info.get("upload_date") or "",
                                    doc_info.get("file_name") or "",
                                    doc_info.get("file_url") or "",
                                    doc_info.get("remarks") or "",
                                    doc_info.get("verified_by") or "",
                                ),
                            )
            conn.commit()
        finally:
            conn.close()

    def _load_from_sqlite(self) -> Optional[Dict[str, Any]]:
        if not os.path.exists(self.sqlite_file):
            return None
        conn = sqlite3.connect(self.sqlite_file)
        try:
            users = [
                {
                    "id": row[0],
                    "email": row[1],
                    "password_hash": row[2],
                    "name": row[3],
                    "mobile_number": row[4],
                    "role": row[5],
                    "profile": json.loads(row[6]) if row[6] else {},
                }
                for row in conn.execute("SELECT id, email, password_hash, name, mobile_number, role, profile FROM users")
            ]
            schemes = [
                {
                    "id": row[0],
                    "name": row[1],
                    "category": row[2],
                    "description": row[3],
                    "benefits": row[4],
                    "criteria": json.loads(row[5]) if row[5] else {},
                    "required_documents": json.loads(row[6]) if row[6] else [],
                    "official_link": row[7],
                    "last_date": row[8],
                    "state_restriction": row[9],
                    "icon": row[10],
                }
                for row in conn.execute("SELECT id, name, category, description, benefits, criteria, required_documents, official_link, last_date, state_restriction, icon FROM schemes")
            ]
            applications = [
                {
                    "id": row[0],
                    "user_id": row[1],
                    "user_name": row[2],
                    "user_email": row[3],
                    "scheme_id": row[4],
                    "scheme_name": row[5],
                    "status": row[6],
                    "applied_date": row[7],
                    "uploaded_documents": json.loads(row[8]) if row[8] else {},
                    "remarks": row[9],
                }
                for row in conn.execute("SELECT id, user_id, user_name, user_email, scheme_id, scheme_name, status, applied_date, uploaded_documents, remarks FROM applications")
            ]
            user_documents = {}
            for row in conn.execute("SELECT user_id, document_name, status, upload_date, file_name, file_url, remarks, verified_by FROM user_documents"):
                user_id, doc_name, status, upload_date, file_name, file_url, remarks, verified_by = row
                user_documents.setdefault(user_id, {})[doc_name] = {
                    "status": status,
                    "upload_date": upload_date,
                    "file_name": file_name,
                    "file_url": file_url,
                    "remarks": remarks,
                    "verified_by": verified_by,
                }
            return {"users": users, "schemes": schemes, "applications": applications, "user_documents": user_documents}
        finally:
            conn.close()

    def _ensure_defaults(self):
        if not hasattr(self, "data") or not isinstance(self.data, dict):
            self.data = {}

        users = self.data.get("users", [])
        if not isinstance(users, list):
            users = []
        if not any(isinstance(u, dict) and u.get("email") == "admin@welfare.gov" for u in users):
            for u in INITIAL_USERS:
                if not any(isinstance(existing, dict) and existing.get("email") == u["email"] for existing in users):
                    users.append(dict(u))
            self.data["users"] = users

        for u in self.data.get("users", []):
            if isinstance(u, dict) and u.get("email") == "admin@welfare.gov" and not u.get("password_hash"):
                u["password_hash"] = "admin123"

    def load_data(self):
        supabase_data = self._load_from_supabase()
        if supabase_data is not None:
            self.data = supabase_data
            self._ensure_defaults()
            return

        if os.path.exists(self.db_file):
            try:
                with open(self.db_file, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
                    self._ensure_defaults()
                    return
            except Exception:
                pass

        sqlite_data = self._load_from_sqlite()
        if sqlite_data is not None and sqlite_data.get("schemes"):
            self.data = sqlite_data
            self._ensure_defaults()
            return

        self.data = {
            "users": INITIAL_USERS,
            "schemes": INITIAL_SCHEMES,
            "applications": [],
            "user_documents": {}
        }
        self._ensure_defaults()

    def save_data(self):
        with open(self.db_file, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)
        self._sync_sqlite_from_json()

    # User operations
    def get_users(self) -> List[Dict[str, Any]]:
        return self.data.get("users", [])

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        for u in self.get_users():
            if u.get("email", "").lower() == email.lower():
                if email.lower() == "admin@welfare.gov" and not u.get("password_hash"):
                    u["password_hash"] = "admin123"
                return u
        return None

    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        for u in self.get_users():
            if u["id"] == user_id:
                return u
        return None

    def add_user(self, user: Dict[str, Any]):
        if self.use_supabase and supabase_db.is_configured():
            try:
                supabase_db.insert_row("users", user)
            except Exception as exc:
                print(f"[Supabase] insert user failed: {exc}")
        self.data["users"].append(user)
        self.save_data()

    def update_user_profile(self, user_id: str, profile: Dict[str, Any]):
        for u in self.data["users"]:
            if u["id"] == user_id:
                u["profile"] = profile
                if self.use_supabase and supabase_db.is_configured():
                    try:
                        supabase_db.update_row("users", {"id": user_id}, {"profile": profile})
                    except Exception as exc:
                        print(f"[Supabase] update profile failed: {exc}")
                self.save_data()
                return u
        return None

    def update_user_password(self, user_id: str, new_password_hash: str) -> bool:
        for u in self.data["users"]:
            if u["id"] == user_id:
                u["password_hash"] = new_password_hash
                if self.use_supabase and supabase_db.is_configured():
                    try:
                        supabase_db.update_row("users", {"id": user_id}, {"password_hash": new_password_hash})
                    except Exception as exc:
                        print(f"[Supabase] update password failed: {exc}")
                self.save_data()
                return True
        return False

    # Scheme operations
    def get_schemes(self) -> List[Dict[str, Any]]:
        if self.use_supabase and supabase_db.is_configured():
            try:
                schemes = supabase_db.fetch_rows("schemes")
                if schemes is not None:
                    self.data["schemes"] = schemes
                    return schemes
            except Exception as exc:
                print(f"[Supabase] fetch schemes error: {exc}")
        return self.data.get("schemes", [])

    def get_scheme_by_id(self, scheme_id: str) -> Optional[Dict[str, Any]]:
        for s in self.get_schemes():
            if s["id"] == scheme_id:
                return s
        return None

    def add_scheme(self, scheme: Dict[str, Any]):
        if self.use_supabase and supabase_db.is_configured():
            try:
                supabase_db.insert_row("schemes", scheme)
            except Exception as exc:
                print(f"[Supabase] insert scheme failed: {exc}")
        self.data["schemes"].append(scheme)
        self.save_data()

    def update_scheme(self, scheme_id: str, updated_data: Dict[str, Any]):
        for i, s in enumerate(self.data.get("schemes", [])):
            if s["id"] == scheme_id:
                self.data["schemes"][i].update(updated_data)
                if self.use_supabase and supabase_db.is_configured():
                    try:
                        supabase_db.update_row("schemes", {"id": scheme_id}, updated_data)
                    except Exception as exc:
                        print(f"[Supabase] update scheme failed: {exc}")
                self.save_data()
                return self.data["schemes"][i]
        return None

    def delete_scheme(self, scheme_id: str) -> bool:
        if self.use_supabase and supabase_db.is_configured():
            try:
                supabase_db.delete_rows("schemes", {"id": scheme_id})
            except Exception as exc:
                print(f"[Supabase] delete scheme failed: {exc}")
        self.data["schemes"] = [s for s in self.data.get("schemes", []) if s.get("id") != scheme_id]
        self.save_data()
        return True

    def get_admin_users(self) -> List[Dict[str, Any]]:
        if self.use_supabase and supabase_db.is_configured():
            try:
                users = supabase_db.fetch_rows("users")
                if users is not None:
                    self.data["users"] = users
                    return users
            except Exception as exc:
                print(f"[Supabase] fetch users error: {exc}")
        return self.data.get("users", [])

    def delete_user(self, user_id: str) -> bool:
        if self.use_supabase and supabase_db.is_configured():
            try:
                supabase_db.delete_rows("users", {"id": user_id})
                supabase_db.delete_rows("user_documents", {"user_id": user_id})
                supabase_db.delete_rows("applications", {"user_id": user_id})
            except Exception as exc:
                print(f"[Supabase] delete user failed: {exc}")
        self.data["users"] = [u for u in self.data.get("users", []) if u.get("id") != user_id]
        if "user_documents" in self.data and user_id in self.data["user_documents"]:
            del self.data["user_documents"][user_id]
        self.data["applications"] = [a for a in self.data.get("applications", []) if a.get("user_id") != user_id]
        self.save_data()
        return True

    def update_user_status(self, user_id: str, is_blocked: bool) -> Optional[Dict[str, Any]]:
        for u in self.data.get("users", []):
            if u["id"] == user_id:
                u["is_blocked"] = is_blocked
                if self.use_supabase and supabase_db.is_configured():
                    try:
                        supabase_db.update_row("users", {"id": user_id}, {"is_blocked": is_blocked})
                    except Exception as exc:
                        print(f"[Supabase] update user status failed: {exc}")
                self.save_data()
                return u
        return None

    # Application operations
    def get_applications(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        if self.use_supabase and supabase_db.is_configured():
            try:
                apps = supabase_db.fetch_rows("applications")
                if apps is not None:
                    self.data["applications"] = apps
            except Exception as exc:
                print(f"[Supabase] fetch applications error: {exc}")

        apps = self.data.get("applications", [])
        if user_id:
            return [a for a in apps if a.get("user_id") == user_id]
        return apps

    def add_application(self, app_data: Dict[str, Any]):
        if self.use_supabase and supabase_db.is_configured():
            try:
                supabase_db.insert_row("applications", app_data)
            except Exception as exc:
                print(f"[Supabase] insert application failed: {exc}")
        self.data["applications"].append(app_data)
        self.save_data()

    def update_application_status(self, app_id: str, status: str, remarks: str = ""):
        for a in self.data.get("applications", []):
            if a["id"] == app_id:
                a["status"] = status
                if remarks:
                    a["remarks"] = remarks
                if self.use_supabase and supabase_db.is_configured():
                    try:
                        supabase_db.update_row("applications", {"id": app_id}, {"status": status, "remarks": a.get("remarks", "")})
                    except Exception as exc:
                        print(f"[Supabase] update application status failed: {exc}")
                self.save_data()
                return a
        return None

    # Document operations
    def get_user_documents(self, user_id: str) -> Dict[str, Any]:
        if self.use_supabase and supabase_db.is_configured():
            try:
                docs = supabase_db.fetch_rows("user_documents", filters={"user_id": user_id})
                if docs is not None:
                    docs_map = {}
                    for doc in docs:
                        docs_map[doc.get("document_name")] = {
                            "status": doc.get("status"),
                            "upload_date": doc.get("upload_date"),
                            "file_name": doc.get("file_name"),
                            "file_url": doc.get("file_url"),
                            "remarks": doc.get("remarks"),
                            "verified_by": doc.get("verified_by"),
                        }
                    return docs_map
            except Exception as exc:
                print(f"[Supabase] fetch user_documents error: {exc}")
        return self.data.get("user_documents", {}).get(user_id, {})

    def update_user_document(self, user_id: str, doc_name: str, doc_info: Dict[str, Any]):
        if "user_documents" not in self.data:
            self.data["user_documents"] = {}
        if user_id not in self.data["user_documents"]:
            self.data["user_documents"][user_id] = {}
        self.data["user_documents"][user_id][doc_name] = doc_info

        if self.use_supabase and supabase_db.is_configured():
            payload = {
                "user_id": user_id,
                "document_name": doc_name,
                "status": doc_info.get("status", "Uploaded"),
                "upload_date": doc_info.get("upload_date"),
                "file_name": doc_info.get("file_name"),
                "file_url": doc_info.get("file_url"),
                "remarks": doc_info.get("remarks"),
                "verified_by": doc_info.get("verified_by"),
            }
            try:
                supabase_db.insert_row("user_documents", payload)
            except Exception:
                try:
                    supabase_db.update_row("user_documents", {"user_id": user_id, "document_name": doc_name}, payload)
                except Exception as exc:
                    print(f"[Supabase] update user document failed: {exc}")
        self.save_data()

    # Notifications operations
    def get_notifications(self, target_user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        notifs = self.data.get("notifications", [
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
        ])
        if target_user_id:
            return [n for n in notifs if n.get("target_user_id") is None or n.get("target_user_id") == target_user_id]
        return notifs

    def add_notification(self, notif_data: Dict[str, Any]):
        if "notifications" not in self.data:
            self.data["notifications"] = []
        self.data["notifications"].insert(0, notif_data)
        self.save_data()

db = Database()

