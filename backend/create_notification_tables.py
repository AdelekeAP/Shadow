"""
Migration script to create notification system tables
Run with: python create_notification_tables.py
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

# SQL to create notification tables
CREATE_NOTIFICATIONS_TABLE = """
CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Content
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    notification_type VARCHAR(50) NOT NULL DEFAULT 'system',
    priority VARCHAR(20) NOT NULL DEFAULT 'medium',

    -- Related entities
    task_id UUID REFERENCES tasks(id) ON DELETE SET NULL,
    course_id UUID REFERENCES courses(id) ON DELETE SET NULL,
    study_plan_id UUID REFERENCES study_plans(id) ON DELETE SET NULL,

    -- Delivery tracking
    channel VARCHAR(20) NOT NULL DEFAULT 'in_app',
    is_read BOOLEAN DEFAULT FALSE,
    is_dismissed BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMP WITH TIME ZONE,

    -- Action handling
    action_url VARCHAR(500),
    action_data JSONB,

    -- Scheduling
    scheduled_for TIMESTAMP WITH TIME ZONE,
    sent_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,

    -- Mood context
    mood_context JSONB,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for notifications
CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_is_read ON notifications(is_read);
CREATE INDEX IF NOT EXISTS idx_notifications_type ON notifications(notification_type);
CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON notifications(created_at DESC);
"""

CREATE_NOTIFICATION_PREFERENCES_TABLE = """
CREATE TABLE IF NOT EXISTS notification_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,

    -- Channel preferences
    email_enabled BOOLEAN DEFAULT TRUE,
    in_app_enabled BOOLEAN DEFAULT TRUE,
    push_enabled BOOLEAN DEFAULT FALSE,

    -- Type preferences
    task_reminders BOOLEAN DEFAULT TRUE,
    task_overdue BOOLEAN DEFAULT TRUE,
    study_plan_updates BOOLEAN DEFAULT TRUE,
    mood_check_reminders BOOLEAN DEFAULT TRUE,
    goal_progress BOOLEAN DEFAULT TRUE,
    achievements BOOLEAN DEFAULT TRUE,
    smart_study BOOLEAN DEFAULT TRUE,
    system_announcements BOOLEAN DEFAULT TRUE,

    -- Timing preferences
    quiet_hours_enabled BOOLEAN DEFAULT FALSE,
    quiet_hours_start VARCHAR(5),
    quiet_hours_end VARCHAR(5),
    timezone VARCHAR(50) DEFAULT 'Africa/Lagos',

    -- Reminder timing
    task_reminder_hours INTEGER DEFAULT 24,
    task_reminder_same_day BOOLEAN DEFAULT TRUE,
    mood_check_frequency VARCHAR(20) DEFAULT 'daily',

    -- Mood-aware preferences
    reduce_when_stressed BOOLEAN DEFAULT TRUE,
    motivate_when_low_energy BOOLEAN DEFAULT TRUE,

    -- Digest preferences
    daily_digest BOOLEAN DEFAULT FALSE,
    weekly_digest BOOLEAN DEFAULT TRUE,
    digest_time VARCHAR(5) DEFAULT '09:00',

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for notification preferences
CREATE INDEX IF NOT EXISTS idx_notification_preferences_user_id ON notification_preferences(user_id);
"""

CREATE_SCHEDULED_REMINDERS_TABLE = """
CREATE TABLE IF NOT EXISTS scheduled_reminders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Reminder details
    reminder_type VARCHAR(50) NOT NULL,
    related_id UUID,

    -- Schedule
    scheduled_time TIMESTAMP WITH TIME ZONE NOT NULL,
    is_recurring BOOLEAN DEFAULT FALSE,
    recurrence_pattern VARCHAR(50),
    recurrence_data JSONB,

    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    is_sent BOOLEAN DEFAULT FALSE,
    last_sent_at TIMESTAMP WITH TIME ZONE,
    next_run_at TIMESTAMP WITH TIME ZONE,

    -- Content customization
    custom_title VARCHAR(255),
    custom_message TEXT,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for scheduled reminders
CREATE INDEX IF NOT EXISTS idx_scheduled_reminders_user_id ON scheduled_reminders(user_id);
CREATE INDEX IF NOT EXISTS idx_scheduled_reminders_scheduled_time ON scheduled_reminders(scheduled_time);
CREATE INDEX IF NOT EXISTS idx_scheduled_reminders_is_active ON scheduled_reminders(is_active);
"""


def create_tables():
    """Create all notification-related tables"""
    with engine.connect() as conn:
        print("Creating notifications table...")
        conn.execute(text(CREATE_NOTIFICATIONS_TABLE))
        conn.commit()
        print("Created notifications table")

        print("Creating notification_preferences table...")
        conn.execute(text(CREATE_NOTIFICATION_PREFERENCES_TABLE))
        conn.commit()
        print("Created notification_preferences table")

        print("Creating scheduled_reminders table...")
        conn.execute(text(CREATE_SCHEDULED_REMINDERS_TABLE))
        conn.commit()
        print("Created scheduled_reminders table")

        print("\nAll notification tables created successfully!")


if __name__ == "__main__":
    create_tables()
