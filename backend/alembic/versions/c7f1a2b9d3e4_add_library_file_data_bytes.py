"""add library file_data + converted_pdf_data byte columns

Stores uploaded library file bytes directly in Postgres so they survive Railway's
ephemeral filesystem (which is wiped on every redeploy). Idempotent so it is safe to
run against environments where the columns were already added manually.

Revision ID: c7f1a2b9d3e4
Revises: a1b2c3d4e5f6
Create Date: 2026-06-05
"""
from alembic import op

# revision identifiers, used by Alembic.
revision = 'c7f1a2b9d3e4'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE library_documents ADD COLUMN IF NOT EXISTS file_data BYTEA")
    op.execute("ALTER TABLE library_documents ADD COLUMN IF NOT EXISTS converted_pdf_data BYTEA")


def downgrade():
    op.execute("ALTER TABLE library_documents DROP COLUMN IF EXISTS converted_pdf_data")
    op.execute("ALTER TABLE library_documents DROP COLUMN IF EXISTS file_data")
