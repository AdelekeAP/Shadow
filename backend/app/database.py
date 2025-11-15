"""
Database configuration and session management
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost:5432/shadow_db")

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Verify connections before using
    echo=True if os.getenv("ENVIRONMENT") == "development" else False
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
    finally:
        db.close()


# Initialize database (create all tables)
def init_db():
    """
    Initialize database - create all tables
    """
    from app.models import user, semester, course, task, mood, gpa, recommendation
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully!")
