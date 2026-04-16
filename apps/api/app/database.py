from pathlib import Path
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


ROOT_DIR = Path(__file__).resolve().parents[3]
DATA_DIR = ROOT_DIR / "data"
DEFAULT_DATABASE_URL = f"sqlite:///{DATA_DIR / 'sgr_mvp.db'}"

def normalize_database_url(raw_url: str) -> str:
    if raw_url.startswith("postgres://"):
        return raw_url.replace("postgres://", "postgresql+psycopg://", 1)
    if raw_url.startswith("postgresql://"):
        return raw_url.replace("postgresql://", "postgresql+psycopg://", 1)
    return raw_url


DATABASE_URL = normalize_database_url(os.getenv("SGR_DATABASE_URL", DEFAULT_DATABASE_URL))

if DATABASE_URL.startswith("sqlite:///"):
    sqlite_path = Path(DATABASE_URL.replace("sqlite:///", "", 1))
    sqlite_path.parent.mkdir(parents=True, exist_ok=True)

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args, future=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
