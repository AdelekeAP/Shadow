"""
Create content curation tables for YouTube/Reddit resource caching
"""
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()


def create_tables():
    """Create curated_resources and content_curation_queries tables"""
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost:5432/shadow_db")
    engine = create_engine(DATABASE_URL)

    with engine.connect() as conn:
        print("🚀 Creating content curation tables...\n")

        # Create curated_resources table
        print("📊 Creating curated_resources table...")
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS curated_resources (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                topic VARCHAR(500) NOT NULL,
                learning_style VARCHAR(50),
                resource_type VARCHAR(50) NOT NULL,
                resource_id VARCHAR(255) NOT NULL,
                url TEXT NOT NULL,
                title VARCHAR(500) NOT NULL,
                description TEXT,
                author VARCHAR(255),
                quality_score NUMERIC(5, 2) NOT NULL,
                platform_scores JSONB,
                cross_referenced VARCHAR(10) NOT NULL DEFAULT 'false',
                engagement_metrics JSONB,
                resource_metadata JSONB,
                has_transcript VARCHAR(10),
                transcript_quality NUMERIC(5, 2),
                cache_expires_at TIMESTAMPTZ,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            )
        """))
        conn.commit()
        print("✅ Created curated_resources table")

        # Create indexes for curated_resources
        print("📊 Creating indexes for curated_resources...")

        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_curated_topic
            ON curated_resources(topic)
        """))

        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_curated_learning_style
            ON curated_resources(learning_style)
        """))

        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_curated_cache_expires
            ON curated_resources(cache_expires_at)
        """))

        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_curated_topic_learning_style
            ON curated_resources(topic, learning_style)
        """))

        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_curated_topic_quality
            ON curated_resources(topic, quality_score)
        """))

        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_curated_resource_type_quality
            ON curated_resources(resource_type, quality_score)
        """))

        conn.commit()
        print("✅ Created indexes for curated_resources")

        # Create content_curation_queries table
        print("📊 Creating content_curation_queries table...")
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS content_curation_queries (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                topic VARCHAR(500) NOT NULL,
                learning_style VARCHAR(50),
                total_resources_found INTEGER DEFAULT 0,
                youtube_count INTEGER DEFAULT 0,
                reddit_count INTEGER DEFAULT 0,
                cross_referenced_count INTEGER DEFAULT 0,
                avg_quality_score NUMERIC(5, 2),
                top_resource_score NUMERIC(5, 2),
                query_duration_ms INTEGER,
                cache_hit VARCHAR(10) NOT NULL DEFAULT 'false',
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """))
        conn.commit()
        print("✅ Created content_curation_queries table")

        # Create indexes for content_curation_queries
        print("📊 Creating indexes for content_curation_queries...")

        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_curation_query_topic
            ON content_curation_queries(topic)
        """))

        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_curation_query_created
            ON content_curation_queries(created_at)
        """))

        conn.commit()
        print("✅ Created indexes for content_curation_queries")

    print("\n✅ All content curation tables created successfully!\n")


if __name__ == "__main__":
    print("\n🚀 Starting content curation database migration...\n")
    create_tables()
    print("✅ Migration complete!\n")
