import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

raw_db_url = os.getenv("DATABASE_URL", "sqlite:///./fasalmitra.db")

# Normalize async driver prefix for synchronous SQLAlchemy engine if needed
if raw_db_url.startswith("postgresql+asyncpg://"):
    DATABASE_URL = raw_db_url.replace("postgresql+asyncpg://", "postgresql://")
else:
    DATABASE_URL = raw_db_url

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    Base.metadata.create_all(bind=engine)
