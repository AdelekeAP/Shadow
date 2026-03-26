"""Add single-column indexes for course_id and semester_id

Revision ID: a1b2c3d4e5f6
Revises: f1a2b3c4d5e6
Create Date: 2026-03-10

"""
from alembic import op

revision = 'a1b2c3d4e5f6'
down_revision = 'f1a2b3c4d5e6'
branch_labels = None
depends_on = None


def upgrade():
    op.create_index('ix_user_courses_course_id', 'user_courses', ['course_id'])
    op.create_index('ix_user_courses_semester_id', 'user_courses', ['semester_id'])


def downgrade():
    op.drop_index('ix_user_courses_semester_id', 'user_courses')
    op.drop_index('ix_user_courses_course_id', 'user_courses')
