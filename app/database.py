import json
import os
from typing import Dict, List, Any, Optional

DB_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data_store.json")

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
        self.load_data()

    def load_data(self):
        if not os.path.exists(self.db_file):
            self.data = {
                "users": INITIAL_USERS,
                "schemes": INITIAL_SCHEMES,
                "applications": [
                    {
                        "id": "app-101",
                        "user_id": "usr-citizen-01",
                        "scheme_id": "scheme-001",
                        "scheme_name": "PM-Kisan Samman Nidhi (PM-KISAN)",
                        "status": "Approved",
                        "applied_date": "2026-03-15",
                        "remarks": "Application verified and approved by District Agriculture Officer."
                    },
                    {
                        "id": "app-102",
                        "user_id": "usr-citizen-01",
                        "scheme_id": "scheme-002",
                        "scheme_name": "Ayushman Bharat PM Jan Arogya Yojana (PM-JAY)",
                        "status": "Under Verification",
                        "applied_date": "2026-06-10",
                        "remarks": "Documents submitted. Pending card issuance."
                    }
                ],
                "user_documents": {
                    "usr-citizen-01": {
                        "Aadhaar Card": {"status": "Verified", "upload_date": "2026-01-10", "file_name": "aadhaar_card.pdf"},
                        "Income Certificate": {"status": "Verified", "upload_date": "2026-02-14", "file_name": "income_certificate.pdf"},
                        "Land Ownership Document (Khatauni/Khasra)": {"status": "Verified", "upload_date": "2026-03-01", "file_name": "land_record.pdf"},
                        "BPL / Ration Card": {"status": "Uploaded", "upload_date": "2026-06-08", "file_name": "bpl_ration_card.pdf"}
                    }
                }
            }
            self.save_data()
        else:
            try:
                with open(self.db_file, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
            except Exception:
                self.data = {
                    "users": INITIAL_USERS,
                    "schemes": INITIAL_SCHEMES,
                    "applications": [],
                    "user_documents": {}
                }
                self.save_data()

    def save_data(self):
        with open(self.db_file, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)

    # User operations
    def get_users(self) -> List[Dict[str, Any]]:
        return self.data.get("users", [])

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        for u in self.get_users():
            if u["email"].lower() == email.lower():
                return u
        return None

    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        for u in self.get_users():
            if u["id"] == user_id:
                return u
        return None

    def add_user(self, user: Dict[str, Any]):
        self.data["users"].append(user)
        self.save_data()

    def update_user_profile(self, user_id: str, profile: Dict[str, Any]):
        for u in self.data["users"]:
            if u["id"] == user_id:
                u["profile"] = profile
                self.save_data()
                return u
        return None

    def update_user_password(self, user_id: str, new_password_hash: str) -> bool:
        for u in self.data["users"]:
            if u["id"] == user_id:
                u["password_hash"] = new_password_hash
                self.save_data()
                return True
        return False

    # Scheme operations
    def get_schemes(self) -> List[Dict[str, Any]]:
        return self.data.get("schemes", [])

    def get_scheme_by_id(self, scheme_id: str) -> Optional[Dict[str, Any]]:
        for s in self.get_schemes():
            if s["id"] == scheme_id:
                return s
        return None

    def add_scheme(self, scheme: Dict[str, Any]):
        self.data["schemes"].append(scheme)
        self.save_data()

    def update_scheme(self, scheme_id: str, updated_data: Dict[str, Any]):
        for i, s in enumerate(self.data["schemes"]):
            if s["id"] == scheme_id:
                self.data["schemes"][i].update(updated_data)
                self.save_data()
                return self.data["schemes"][i]
        return None

    def delete_scheme(self, scheme_id: str) -> bool:
        initial_len = len(self.data["schemes"])
        self.data["schemes"] = [s for s in self.data["schemes"] if s["id"] != scheme_id]
        if len(self.data["schemes"]) < initial_len:
            self.save_data()
            return True
        return False

    # Application operations
    def get_applications(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        apps = self.data.get("applications", [])
        if user_id:
            return [a for a in apps if a.get("user_id") == user_id]
        return apps

    def add_application(self, app_data: Dict[str, Any]):
        self.data["applications"].append(app_data)
        self.save_data()

    def update_application_status(self, app_id: str, status: str, remarks: str = ""):
        for a in self.data["applications"]:
            if a["id"] == app_id:
                a["status"] = status
                if remarks:
                    a["remarks"] = remarks
                self.save_data()
                return a
        return None

    # Document operations
    def get_user_documents(self, user_id: str) -> Dict[str, Any]:
        return self.data.get("user_documents", {}).get(user_id, {})

    def update_user_document(self, user_id: str, doc_name: str, doc_info: Dict[str, Any]):
        if "user_documents" not in self.data:
            self.data["user_documents"] = {}
        if user_id not in self.data["user_documents"]:
            self.data["user_documents"][user_id] = {}
        self.data["user_documents"][user_id][doc_name] = doc_info
        self.save_data()

db = Database()
