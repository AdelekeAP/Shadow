"""
Initialize SmartStudy database tables
Run this script to create all new SmartStudy tables
"""
from app.database import engine, Base, init_db
from app.models import *

if __name__ == "__main__":
    print("🔧 Creating SmartStudy database tables...")
    print(f"📊 Database URL: {engine.url}")

    try:
        # Create all tables (will skip existing tables)
        Base.metadata.create_all(bind=engine)
        print("\n✅ SmartStudy database tables created successfully!")

        # List all tables
        print("\n📋 Tables created:")
        for table in Base.metadata.sorted_tables:
            print(f"   - {table.name}")

    except Exception as e:
        print(f"\n❌ Error creating tables: {e}")
        raise
