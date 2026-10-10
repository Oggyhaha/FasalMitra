import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
LOCAL_DB_PATH = ROOT_DIR / "fasalmitra.db"
LOCAL_DB_URL = f"sqlite:///{LOCAL_DB_PATH.as_posix()}"

raw_db_url = os.getenv("DATABASE_URL", LOCAL_DB_URL)

# Normalize async driver prefix for synchronous SQLAlchemy engine if needed
if raw_db_url.startswith("postgresql+asyncpg://"):
    DATABASE_URL = raw_db_url.replace("postgresql+asyncpg://", "postgresql://")
else:
    DATABASE_URL = raw_db_url

# If DATABASE_URL is SQLite, ensure it points to the absolute workspace path
if DATABASE_URL.startswith("sqlite"):
    DATABASE_URL = LOCAL_DB_URL

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {"connect_timeout": 3}

try:
    engine = create_engine(DATABASE_URL, connect_args=connect_args, echo=False)
    with engine.connect() as conn:
        pass
except Exception as e:
    print(f"[DB Engine] Notice: Remote DATABASE_URL connection failed ({e}). Falling back to local SQLite at {LOCAL_DB_PATH}", flush=True)
    DATABASE_URL = LOCAL_DB_URL
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False}, echo=False)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    import backend.app.db.models  # ensure models are registered
    Base.metadata.create_all(bind=engine)

# Auto-ensure tables exist
try:
    init_db()
except Exception:
    pass
