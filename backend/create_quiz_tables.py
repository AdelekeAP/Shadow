"""
Migration script to create quiz tables
Run with: python create_quiz_tables.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("ERROR: DATABASE_URL not set")
    sys.exit(1)

engine = create_engine(DATABASE_URL)

CREATE_QUIZZES_TABLE = """
CREATE TABLE IF NOT EXISTS quizzes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    study_plan_id UUID REFERENCES study_plans(id) ON DELETE SET NULL,
    course_id UUID REFERENCES courses(id) ON DELETE SET NULL,

    title VARCHAR(255) NOT NULL,
    topic VARCHAR(255) NOT NULL,
    quiz_type VARCHAR(50) NOT NULL,

    questions JSONB NOT NULL,
    question_count INTEGER NOT NULL,
    time_limit_minutes INTEGER,
    difficulty_level VARCHAR(50),
    source_type VARCHAR(50) NOT NULL,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_quizzes_user_id ON quizzes(user_id);
CREATE INDEX IF NOT EXISTS idx_quizzes_topic ON quizzes(topic);
"""

CREATE_QUIZ_ATTEMPTS_TABLE = """
CREATE TABLE IF NOT EXISTS quiz_attempts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    quiz_id UUID NOT NULL REFERENCES quizzes(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    answers JSONB NOT NULL,
    score NUMERIC(5, 2) NOT NULL,
    correct_count INTEGER NOT NULL,
    total_questions INTEGER NOT NULL,

    time_taken_seconds INTEGER,
    was_timed BOOLEAN DEFAULT FALSE,
    timed_out BOOLEAN DEFAULT FALSE,

    knowledge_gaps JSONB,

    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_quiz_attempts_quiz_id ON quiz_attempts(quiz_id);
CREATE INDEX IF NOT EXISTS idx_quiz_attempts_user_id ON quiz_attempts(user_id);
"""


def create_tables():
    with engine.connect() as conn:
        print("Creating quizzes table...")
        conn.execute(text(CREATE_QUIZZES_TABLE))
        conn.commit()
        print("Created quizzes table")

        print("Creating quiz_attempts table...")
        conn.execute(text(CREATE_QUIZ_ATTEMPTS_TABLE))
        conn.commit()
        print("Created quiz_attempts table")

        print("\nAll quiz tables created successfully!")


if __name__ == "__main__":
    create_tables()
