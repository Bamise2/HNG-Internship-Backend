from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
import logging

load_dotenv()
logger = logging.getLogger(__name__)

# ------------------------------------------------------------------------------
# DATABASE URL HANDLING
# ------------------------------------------------------------------------------

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    # Fallback for local dev
    logger.warning("⚠️ DATABASE_URL not found in environment, using local MySQL instance.")
    DATABASE_URL = "mysql+pymysql://root:@localhost:3306/country_api"

# Railway sometimes provides the URL in a slightly different variable
if DATABASE_URL.startswith("mysql://"):
    # SQLAlchemy expects "mysql+pymysql://"
    DATABASE_URL = DATABASE_URL.replace("mysql://", "mysql+pymysql://")

# ------------------------------------------------------------------------------
# DATABASE ENGINE & SESSION
# ------------------------------------------------------------------------------
try:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,   # prevents "MySQL server has gone away" issues
        pool_recycle=280,     # helps with idle connection timeouts
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()
except Exception as e:
    logger.error(f"❌ Failed to create SQLAlchemy engine: {e}")
    raise e


# ------------------------------------------------------------------------------
# DB DEPENDENCY
# ------------------------------------------------------------------------------
def get_db():
    """Dependency to provide a DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ------------------------------------------------------------------------------
# INITIALIZATION
# ------------------------------------------------------------------------------
def init_db():
    """Initialize database tables (runs once on startup)."""
    from app.models import country  # ensure models are imported
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created successfully.")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
