"""
Convert all existing PPTX files in the library to PDF
Run this once to convert existing PowerPoint files uploaded before conversion was implemented
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import logging

from app.models.library import LibraryDocument
from app.services.document_converter import convert_pptx_to_pdf

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def convert_existing_pptx_files():
    """Find and convert all existing PPTX files in the library"""
    try:
        # Get database URL from environment
        DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost:5432/shadow_db")

        # Create engine and session
        engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()

        # Find all PPTX documents without converted PDFs
        pptx_docs = db.query(LibraryDocument).filter(
            LibraryDocument.file_type.in_(['pptx', 'ppt']),
            LibraryDocument.converted_pdf_path == None
        ).all()

        if not pptx_docs:
            logger.info("✅ No PPTX files need conversion")
            return

        logger.info(f"📊 Found {len(pptx_docs)} PPTX files to convert")

        converted_count = 0
        failed_count = 0

        for doc in pptx_docs:
            try:
                logger.info(f"\n🔄 Converting: {doc.file_name} (ID: {doc.id})")

                # Check if original file exists
                if not os.path.exists(doc.file_path):
                    logger.error(f"❌ Original file not found: {doc.file_path}")
                    failed_count += 1
                    continue

                # Convert to PDF
                converted_pdf_path = convert_pptx_to_pdf(doc.file_path)

                # Update database
                doc.converted_pdf_path = converted_pdf_path
                db.commit()

                logger.info(f"✅ Converted: {doc.file_name}")
                logger.info(f"   PDF saved to: {converted_pdf_path}")
                converted_count += 1

            except Exception as e:
                logger.error(f"❌ Failed to convert {doc.file_name}: {e}")
                failed_count += 1
                db.rollback()
                continue

        logger.info(f"\n{'='*60}")
        logger.info(f"📈 Conversion Summary:")
        logger.info(f"   ✅ Successfully converted: {converted_count}")
        logger.info(f"   ❌ Failed: {failed_count}")
        logger.info(f"   📊 Total processed: {len(pptx_docs)}")
        logger.info(f"{'='*60}\n")

        db.close()

    except Exception as e:
        logger.error(f"❌ Error in conversion script: {e}")
        raise


if __name__ == "__main__":
    print("\n🚀 Starting conversion of existing PPTX files...\n")
    convert_existing_pptx_files()
    print("\n✅ Conversion script complete!\n")
