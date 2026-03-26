"""
Database configuration and session management
"""
import logging
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    if os.getenv("ENVIRONMENT") == "production":
        raise RuntimeError("DATABASE_URL must be set in production")
    DATABASE_URL = "postgresql://localhost:5432/shadow_db"

# SSL/TLS configuration for production database connections
_connect_args = {}
_ssl_mode = os.getenv("DB_SSL_MODE")
if _ssl_mode:
    _ssl_cert_path = os.getenv("DB_SSL_CERT_PATH")
    ssl_ctx = {}
    if _ssl_mode in ("require", "verify-ca", "verify-full"):
        ssl_ctx["sslmode"] = _ssl_mode
    if _ssl_cert_path:
        ssl_ctx["sslrootcert"] = _ssl_cert_path
    _connect_args = ssl_ctx
    logger.info(f"Database SSL enabled: sslmode={_ssl_mode}")

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Verify connections before using
    pool_size=int(os.getenv("DB_POOL_SIZE", "20")),
    max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "10")),
    pool_recycle=1800,
    pool_timeout=30,
    echo=False,
    connect_args=_connect_args if _connect_args else {},
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()


# Dependency to get database session
def get_db():
    """
    Dependency function to get database session
    Usage in FastAPI routes: db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# Initialize database (create all tables)
def init_db():
    """
    Initialize database - create all tables
    """
    from app.models import user, course, task, mood, smartstudy
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")
