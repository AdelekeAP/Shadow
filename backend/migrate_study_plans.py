"""
Database Migration: Add completed_days and learning_style_used to study_plans
Run this once to update the database schema
"""
from app.database import engine
from sqlalchemy import text

def run_migration():
    print("🔧 Running Study Plans Migration...")
    print("=" * 60)

    try:
        with engine.connect() as conn:
            # Check if columns already exist
            check_sql = text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name='study_plans'
                AND column_name IN ('completed_days', 'learning_style_used')
            """)

            result = conn.execute(check_sql)
            existing_columns = [row[0] for row in result]

            if 'completed_days' in existing_columns and 'learning_style_used' in existing_columns:
                print("✅ Migration already applied - columns exist!")
                return True

            # Add completed_days column
            if 'completed_days' not in existing_columns:
                print("\n📊 Adding 'completed_days' column...")
                conn.execute(text("""
                    ALTER TABLE study_plans
                    ADD COLUMN completed_days JSONB DEFAULT '[]'::jsonb
                """))
                conn.commit()
                print("✅ 'completed_days' column added!")

            # Add learning_style_used column
            if 'learning_style_used' not in existing_columns:
                print("\n🎨 Adding 'learning_style_used' column...")
                conn.execute(text("""
                    ALTER TABLE study_plans
                    ADD COLUMN learning_style_used VARCHAR(50)
                """))
                conn.commit()
                print("✅ 'learning_style_used' column added!")

            print("\n" + "=" * 60)
            print("🎉 MIGRATION COMPLETE!")
            print("=" * 60)

            # Show updated schema
            print("\n📋 Study Plans Table Schema:")
            schema_sql = text("""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name='study_plans'
                ORDER BY ordinal_position
            """)

            result = conn.execute(schema_sql)
            for row in result:
                print(f"   - {row[0]}: {row[1]}")

            return True

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        return False


if __name__ == "__main__":
    success = run_migration()
    if success:
        print("\n✅ You can now use the study plan progress tracking!")
    else:
        print("\n❌ Migration failed - check error above")
