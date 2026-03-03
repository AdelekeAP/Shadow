"""
Add missing columns to study_plans table
Adds: learning_style_used, completed_days
"""
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

def migrate():
    """Add learning_style_used and completed_days columns to study_plans table"""
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost:5432/shadow_db")
    engine = create_engine(DATABASE_URL)

    with engine.connect() as conn:
        # Check if learning_style_used column exists
        result = conn.execute(text("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name='study_plans' AND column_name='learning_style_used'
        """))

        if not result.fetchone():
            print("📊 Adding learning_style_used column...")
            conn.execute(text("""
                ALTER TABLE study_plans ADD COLUMN learning_style_used VARCHAR(50)
            """))
            conn.commit()
            print("✅ Added learning_style_used column")
        else:
            print("✓ learning_style_used column already exists")

        # Check if completed_days column exists
        result = conn.execute(text("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name='study_plans' AND column_name='completed_days'
        """))

        if not result.fetchone():
            print("📊 Adding completed_days column...")
            conn.execute(text("""
                ALTER TABLE study_plans ADD COLUMN completed_days JSONB DEFAULT '[]'::jsonb
            """))
            conn.commit()
            print("✅ Added completed_days column")
        else:
            print("✓ completed_days column already exists")

    print("\n✅ Migration complete!")

if __name__ == "__main__":
    print("\n🚀 Starting database migration...\n")
    migrate()
