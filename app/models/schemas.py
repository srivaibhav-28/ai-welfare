from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class UserRegister(BaseModel):
    name: str
    email: str
    mobile_number: str = ""
    password: str
    confirm_password: Optional[str] = None
    confirm: Optional[str] = None
    role: str = "citizen"
    invite_code: Optional[str] = None

class UserLogin(BaseModel):
    email: str
    password: str

class ChangePassword(BaseModel):
    old_password: str
    new_password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    name: str
    email: str
    mobile_number: str = ""
    role: str
    is_verified: bool = True
    picture: Optional[str] = None
    is_first_time: bool = False
    has_completed_profile: bool = False

class OTPVerifyRequest(BaseModel):
    email: str
    otp: str

class OTPResendRequest(BaseModel):
    email: str

class GoogleAuthRequest(BaseModel):
    email: str
    name: str
    google_id: Optional[str] = None
    user_id: Optional[str] = None
    id: Optional[str] = None
    picture: Optional[str] = None
    role: str = "citizen"

class CitizenProfile(BaseModel):
    name: str = ""
    mobile_number: str = ""
    aadhaar_number: str = ""
    dob: str = ""
    age: int = Field(default=25, ge=0, le=120)
    gender: str = "Male"
    marital_status: str = "Single"  # Single, Married, Widow, Divorced
    state: str = "Uttar Pradesh"
    district: str = "Varanasi"
    mandal: str = ""
    village: str = ""
    pincode: str = ""
    occupation: str = "Farmer"
    annual_income: float = Field(default=150000, ge=0)
    family_income: float = Field(default=150000, ge=0)
    bank_account_number: str = ""
    ifsc_code: str = ""
    education: str = "Secondary"
    caste_category: str = "General"  # General, OBC, SC, ST, EWS
    minority_status: bool = False
    disability_status: bool = False
    student_status: bool = False
    farmer_status: bool = False
    senior_citizen_status: bool = False
    widow_status: bool = False
    bpl_status: bool = False
    unemployed_status: bool = False
    aadhaar_available: bool = True
    bank_account_available: bool = True
    rural_urban: str = "Rural"
    profile_completed: bool = False
    saved_schemes: List[str] = Field(default_factory=list)

class SchemeCreate(BaseModel):
    name: str
    category: str
    description: str
    benefits: str
    criteria: Dict[str, Any]
    required_documents: List[str]
    official_link: str
    last_date: str = "Open"
    state_restriction: str = "All"
    icon: str = "bookmark"

class SchemeUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    benefits: Optional[str] = None
    criteria: Optional[Dict[str, Any]] = None
    required_documents: Optional[List[str]] = None
    official_link: Optional[str] = None
    last_date: Optional[str] = None
    state_restriction: Optional[str] = None
    icon: Optional[str] = None

class ApplicationCreate(BaseModel):
    scheme_id: str
    uploaded_documents: Optional[Dict[str, str]] = Field(default_factory=dict)

class ApplicationStatusUpdate(BaseModel):
    status: str  # Applied, Under Verification, Approved, Rejected
    remarks: str = ""

class ChatRequest(BaseModel):
    message: str
    language: str = "en"  # en, hi, te
    profile_data: Optional[Dict[str, Any]] = None

class DocumentStatusUpdate(BaseModel):
    document_name: str
    status: str  # Uploaded, Verified, Missing, Rejected
    file_name: Optional[str] = None
    remarks: Optional[str] = None

class DocumentVerifyRequest(BaseModel):
    user_id: str
    document_name: str
    status: str  # Verified, Rejected
    remarks: str = ""

class UserStatusUpdate(BaseModel):
    is_blocked: bool

class NotificationCreate(BaseModel):
    title: str
    message: str
    target_user_id: Optional[str] = None  # None for broadcast to all users
    type: str = "info"  # info, success, warning, alert

class SchemeRuleUpdate(BaseModel):
    criteria: Dict[str, Any]
    required_documents: Optional[List[str]] = None

class AppOtpInitiateRequest(BaseModel):
    scheme_id: str
    uploaded_documents: Optional[Dict[str, str]] = None

class AppOtpVerifyRequest(BaseModel):
    scheme_id: str
    otp: str
    uploaded_documents: Optional[Dict[str, str]] = None
