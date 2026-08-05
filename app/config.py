import os
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

class Config:
    SUPABASE_URL: str = os.environ.get("SUPABASE_URL", "").strip()
    SUPABASE_ANON_KEY: str = (
        os.environ.get("SUPABASE_ANON_KEY")
        or os.environ.get("SUPABASE_PUBLISHABLE_KEY", "")
    ).strip()
    SUPABASE_SERVICE_ROLE_KEY: str = (
        os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        or os.environ.get("SUPABASE_ANON_KEY")
        or os.environ.get("SUPABASE_PUBLISHABLE_KEY", "")
    ).strip()
    DATABASE_URL: str = (
        os.environ.get("DATABASE_URL")
        or os.environ.get("DIRECT_URL", "")
    ).strip()
    SECRET_KEY: str = os.environ.get("SECRET_KEY", "ai_welfare_eligibility_secret_jwt_key").strip()
    
    # Supabase Storage Configuration
    SUPABASE_STORAGE_BUCKET: str = os.environ.get("SUPABASE_STORAGE_BUCKET", "scheme-documents").strip()
    ENABLE_SUPABASE_STORAGE: bool = os.environ.get("ENABLE_SUPABASE_STORAGE", "true").lower() == "true"

config = Config()
