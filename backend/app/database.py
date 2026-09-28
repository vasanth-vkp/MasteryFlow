import os
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Database path in backend directory
DB_PATH = os.environ.get("DB_PATH", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "masteryflow.db"))
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_utc_now() -> datetime.datetime:
    """Returns timezone-naive UTC datetime for SQLite compatibility without Python 3.14 deprecation warnings."""
    return datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
