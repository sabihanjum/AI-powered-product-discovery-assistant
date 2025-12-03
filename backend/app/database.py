import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Get the directory where this file is located
BASE_DIR = Path(__file__).resolve().parent.parent  # backend/

# Prefer DATABASE_URL (Postgres), otherwise fall back to local SQLite for quick testing.
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    # Handle SQLite URLs specially (need check_same_thread for SQLite)
    if DATABASE_URL.startswith("sqlite"):
        engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False}, echo=False)
    else:
        engine = create_engine(DATABASE_URL, echo=False)
else:
    # Use absolute path to dev.db in the backend folder
    db_path = BASE_DIR / "dev.db"
    sqlite_url = f"sqlite:///{db_path}"
    print(f"Using SQLite database at: {db_path}")
    engine = create_engine(sqlite_url, connect_args={"check_same_thread": False}, echo=False)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
