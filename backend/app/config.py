import os
from pydantic_settings import BaseSettings

class Settings:
    PROJECT_NAME: str = "FasalMitra"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./fasalmitra.db")
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
    
    # Data.gov.in API Key
    DATA_GOV_IN_API_KEY: str = os.getenv("DATA_GOV_IN_API_KEY", "")
    
    # API Credentials & Flags
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    TWILIO_ACCOUNT_SID: str = os.getenv("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH_TOKEN", "")
    WEATHER_API_KEY: str = os.getenv("WEATHER_API_KEY", "")
    INDIC_TRANS2_ENDPOINT: str = os.getenv("INDIC_TRANS2_ENDPOINT", "")
    
    # Mode
    USE_MOCK_FALLBACK: bool = os.getenv("USE_MOCK_FALLBACK", "true").lower() == "true"

settings = Settings()
