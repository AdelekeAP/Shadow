"""Add scan_status column and GIN trigram indexes for full-text search

Revision ID: c4d5e6f7g8h9
Revises: 6211460164fa
Create Date: 2026-03-04
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "c4d5e6f7g8h9"
down_revision: Union[str, Sequence[str], None] = "6211460164fa"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Add scan_status column with default 'clean' for existing rows
    op.add_column(
        "library_documents",
        sa.Column("scan_status", sa.String(10), nullable=False, server_default="clean"),
    )

    # 2. Enable pg_trgm extension for trigram-based GIN indexes
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    # 3. Add GIN trigram indexes for fast ILIKE search
    op.execute(
        "CREATE INDEX ix_library_documents_topic_gin ON library_documents "
        "USING gin (topic gin_trgm_ops)"
    )
    op.execute(
        "CREATE INDEX ix_library_documents_file_name_gin ON library_documents "
        "USING gin (file_name gin_trgm_ops)"
    )
    op.execute(
        "CREATE INDEX ix_library_documents_extracted_text_gin ON library_documents "
        "USING gin (extracted_text gin_trgm_ops)"
    )

    # 4. Add index on scan_status for filtering
    op.create_index("ix_library_documents_scan_status", "library_documents", ["scan_status"])


def downgrade() -> None:
    op.drop_index("ix_library_documents_scan_status", table_name="library_documents")
    op.execute("DROP INDEX IF EXISTS ix_library_documents_extracted_text_gin")
    op.execute("DROP INDEX IF EXISTS ix_library_documents_file_name_gin")
    op.execute("DROP INDEX IF EXISTS ix_library_documents_topic_gin")
    op.drop_column("library_documents", "scan_status")
