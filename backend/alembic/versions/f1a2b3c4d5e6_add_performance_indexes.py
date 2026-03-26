"""Add performance indexes

Revision ID: f1a2b3c4d5e6
Revises: e1f2a3b4c5d6
Create Date: 2026-03-10

"""
from alembic import op

revision = 'f1a2b3c4d5e6'
down_revision = 'e1f2a3b4c5d6'
branch_labels = None
depends_on = None


def upgrade():
    op.create_index('ix_tasks_user_id', 'tasks', ['user_id'])
    op.create_index('ix_tasks_user_course_id', 'tasks', ['user_course_id'])
    op.create_index('ix_user_courses_user_course', 'user_courses', ['user_id', 'course_id'])
    op.create_index('ix_user_courses_user_semester', 'user_courses', ['user_id', 'semester_id'])


def downgrade():
    op.drop_index('ix_tasks_user_course_id', 'tasks')
    op.drop_index('ix_tasks_user_id', 'tasks')
    op.drop_index('ix_user_courses_user_course', 'user_courses')
    op.drop_index('ix_user_courses_user_semester', 'user_courses')
