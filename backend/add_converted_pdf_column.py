"""
Database Migration: Add converted_pdf_path column to library_documents table

Run this script once to update the database schema:
    python add_converted_pdf_column.py
"""
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv
import logging

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate():
    """Add converted_pdf_path column to library_documents table"""
    try:
        # Get database URL from environment
        DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost:5432/shadow_db")

        # Create engine
        engine = create_engine(DATABASE_URL)

        with engine.connect() as conn:
            # Check if column already exists
            result = conn.execute(text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name='library_documents'
                AND column_name='converted_pdf_path'
            """))

            if result.fetchone():
                logger.info("✅ Column 'converted_pdf_path' already exists")
                return

            # Add the column
            logger.info("🔄 Adding 'converted_pdf_path' column...")
            conn.execute(text("""
                ALTER TABLE library_documents
                ADD COLUMN converted_pdf_path TEXT
            """))
            conn.commit()

            logger.info("✅ Successfully added 'converted_pdf_path' column")

    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        raise


if __name__ == "__main__":
    migrate()
    print("\n✅ Migration complete!")
