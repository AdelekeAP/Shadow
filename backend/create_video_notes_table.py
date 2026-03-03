"""
Migration script to create the video_notes table
Run: python create_video_notes_table.py
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from app.database import engine

# SQL to create the video_notes table
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS video_notes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    resource_id UUID NOT NULL REFERENCES study_plan_resources(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    timestamp_seconds INTEGER,
    note_type VARCHAR(50) DEFAULT 'note',
    color VARCHAR(20) DEFAULT 'yellow',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for faster lookups
CREATE INDEX IF NOT EXISTS idx_video_notes_user_id ON video_notes(user_id);
CREATE INDEX IF NOT EXISTS idx_video_notes_resource_id ON video_notes(resource_id);
CREATE INDEX IF NOT EXISTS idx_video_notes_created_at ON video_notes(created_at);
"""

def main():
    print("Creating video_notes table...")

    with engine.connect() as conn:
        # Execute the create table SQL
        conn.execute(text(CREATE_TABLE_SQL))
        conn.commit()

        # Verify table exists
        result = conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'video_notes'
            );
        """))
        exists = result.scalar()

        if exists:
            print("✅ video_notes table created successfully!")
        else:
            print("❌ Failed to create video_notes table")
            return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
