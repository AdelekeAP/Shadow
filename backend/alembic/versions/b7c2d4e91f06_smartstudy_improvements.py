"""smartstudy improvements: article reports + audio summaries

Revision ID: b7c2d4e91f06
Revises: a3f8b2c91e04
Create Date: 2026-03-01 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'b7c2d4e91f06'
down_revision: Union[str, Sequence[str], None] = 'a3f8b2c91e04'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add report tracking and audio summary columns to study_plan_resources."""
    # Phase A: Report tracking
    op.add_column('study_plan_resources', sa.Column('report_reason', sa.String(50), nullable=True))
    op.add_column('study_plan_resources', sa.Column('reported_at', sa.DateTime(timezone=True), nullable=True))

    # Phase B: Audio summaries
    op.add_column('study_plan_resources', sa.Column('audio_file_path', sa.String(500), nullable=True))
    op.add_column('study_plan_resources', sa.Column('audio_script', sa.Text(), nullable=True))
    op.add_column('study_plan_resources', sa.Column('audio_generated_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    """Remove report tracking and audio summary columns."""
    op.drop_column('study_plan_resources', 'audio_generated_at')
    op.drop_column('study_plan_resources', 'audio_script')
    op.drop_column('study_plan_resources', 'audio_file_path')
    op.drop_column('study_plan_resources', 'reported_at')
    op.drop_column('study_plan_resources', 'report_reason')
