-- Shadow Database Schema
-- PAU-Specific Academic Achievement System
-- PostgreSQL 15+

-- Create database (run this separately)
-- CREATE DATABASE shadow_db;

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- TABLE: users
-- ============================================
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    university_id VARCHAR(50),
    entry_level VARCHAR(10), -- '100L', '200L-DE', '300L', '400L'
    gpa_scale DECIMAL(3,1) DEFAULT 5.0, -- PAU uses 5.0
    target_cgpa DECIMAL(3,2), -- User's goal (e.g., 4.50)
    current_cgpa DECIMAL(3,2),
    total_credits_completed INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_university_id ON users(university_id);

-- ============================================
-- TABLE: semesters
-- ============================================
CREATE TABLE semesters (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(50) NOT NULL, -- 'Fall 2024', 'Spring 2025'
    academic_year VARCHAR(20), -- '2024/2025'
    semester_number INTEGER, -- 1 for First Semester, 2 for Second
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    target_gpa DECIMAL(3,2), -- Semester-specific goal
    actual_gpa DECIMAL(3,2), -- Final semester GPA
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_semesters_user_active ON semesters(user_id, is_active);

-- ============================================
-- TABLE: courses
-- ============================================
CREATE TABLE courses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code VARCHAR(20) NOT NULL UNIQUE, -- 'CSC401', 'PAU-CSC411'
    title VARCHAR(255) NOT NULL,
    credits INTEGER NOT NULL,
    level VARCHAR(10), -- '400'
    status VARCHAR(20) DEFAULT 'C', -- 'C' (Compulsory), 'E' (Elective), 'R' (Required)
    department VARCHAR(100) DEFAULT 'Computer Science',
    description TEXT,
    created_by VARCHAR(10) DEFAULT 'admin', -- 'admin' or 'user'
    is_approved BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_courses_code ON courses(code);
CREATE INDEX idx_courses_level ON courses(level);
CREATE INDEX idx_courses_department ON courses(department);

-- ============================================
-- TABLE: user_courses
-- ============================================
CREATE TABLE user_courses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    semester_id UUID REFERENCES semesters(id) ON DELETE CASCADE,
    course_id UUID REFERENCES courses(id) ON DELETE CASCADE,
    is_carryover BOOLEAN DEFAULT false,
    is_priority BOOLEAN DEFAULT false,

    -- PAU-specific fields (35/65 split)
    ca_score DECIMAL(5,2) DEFAULT 0, -- Current CA out of 35
    participation_score DECIMAL(5,2), -- Out of 5
    exam_score DECIMAL(5,2), -- Out of 65 (if taken)
    predicted_exam_score DECIMAL(5,2), -- Predicted exam score

    -- Overall grades
    current_score DECIMAL(5,2), -- CA + Exam (if taken)
    predicted_score DECIMAL(5,2), -- CA + Predicted Exam
    current_grade_point DECIMAL(3,2), -- 0.0-5.0 (if final)
    predicted_grade_point DECIMAL(3,2), -- Predicted GP
    letter_grade VARCHAR(2), -- 'A', 'B', 'C', etc.
    predicted_letter_grade VARCHAR(2),

    completion_rate DECIMAL(5,2), -- Percentage of tasks completed
    enrolled_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(user_id, semester_id, course_id)
);

CREATE INDEX idx_user_courses_user_semester ON user_courses(user_id, semester_id);
CREATE INDEX idx_user_courses_predictions ON user_courses(predicted_grade_point);

-- ============================================
-- TABLE: tasks
-- ============================================
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    user_course_id UUID REFERENCES user_courses(id) ON DELETE CASCADE,

    -- Task details
    title VARCHAR(255) NOT NULL,
    description TEXT,
    task_type VARCHAR(50) NOT NULL, -- 'test', 'project', 'participation', 'exam'

    -- PAU-specific grading
    weight DECIMAL(5,2) NOT NULL, -- Marks (e.g., 15 for Test 1)
    max_marks DECIMAL(5,2), -- Usually same as weight
    earned_marks DECIMAL(5,2), -- Actual score received
    category VARCHAR(10), -- 'CA' or 'EXAM'

    -- Timing
    due_date TIMESTAMP,
    completed_at TIMESTAMP,
    is_completed BOOLEAN DEFAULT false,
    is_late BOOLEAN DEFAULT false,

    -- Effort tracking
    effort_estimate INTEGER, -- Minutes
    actual_effort INTEGER, -- Minutes (user feedback)

    -- Priority
    priority_score DECIMAL(5,2), -- Calculated by system
    is_urgent BOOLEAN DEFAULT false,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_tasks_user_course ON tasks(user_course_id);
CREATE INDEX idx_tasks_due_date ON tasks(due_date);
CREATE INDEX idx_tasks_completion ON tasks(is_completed);
CREATE INDEX idx_tasks_priority ON tasks(priority_score DESC);

-- ============================================
-- TABLE: moods
-- ============================================
CREATE TABLE moods (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,

    mood_type VARCHAR(50) NOT NULL, -- 'focused', 'tired', 'stressed', 'neutral', 'motivated', 'overwhelmed'
    mood_text TEXT, -- Optional text note
    sentiment_score DECIMAL(3,2), -- -1.0 to 1.0 (from NLP)
    energy_level INTEGER, -- 1-5 scale

    -- Context
    associated_task_id UUID REFERENCES tasks(id) ON DELETE SET NULL,
    associated_course_id UUID REFERENCES user_courses(id) ON DELETE SET NULL,

    logged_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_moods_user_date ON moods(user_id, logged_at DESC);
CREATE INDEX idx_moods_sentiment ON moods(sentiment_score);

-- ============================================
-- TABLE: gpa_records
-- ============================================
CREATE TABLE gpa_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    semester_id UUID REFERENCES semesters(id),

    semester_gpa DECIMAL(3,2),
    cumulative_gpa DECIMAL(3,2),
    predicted_cgpa DECIMAL(3,2),

    total_credits INTEGER,
    credits_this_semester INTEGER,

    -- PAU-specific
    classification VARCHAR(50), -- 'First Class', 'Second Class Upper', etc.
    target_cgpa DECIMAL(3,2),
    gap_to_target DECIMAL(3,2), -- target - predicted

    recorded_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_gpa_records_user_date ON gpa_records(user_id, recorded_at DESC);

-- ============================================
-- TABLE: recommendations
-- ============================================
CREATE TABLE recommendations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,

    recommendation_type VARCHAR(50), -- 'urgent', 'mood_based', 'goal_driven', 'recovery'
    recommendation_reason TEXT,
    priority_rank INTEGER,

    is_active BOOLEAN DEFAULT true,
    is_dismissed BOOLEAN DEFAULT false,

    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,
    acted_on_at TIMESTAMP
);

CREATE INDEX idx_recommendations_user_active ON recommendations(user_id, is_active);
CREATE INDEX idx_recommendations_priority ON recommendations(priority_rank);

-- ============================================
-- Trigger to update updated_at timestamp
-- ============================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_user_courses_updated_at BEFORE UPDATE ON user_courses
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tasks_updated_at BEFORE UPDATE ON tasks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
