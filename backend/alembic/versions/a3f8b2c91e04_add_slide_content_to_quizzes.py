"""add slide_content to quizzes

Revision ID: a3f8b2c91e04
Revises: 41d16dc059db
Create Date: 2026-03-01 00:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'a3f8b2c91e04'
down_revision: Union[str, Sequence[str], None] = '41d16dc059db'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add slide_content column to quizzes table for preserving uploaded document text."""
    op.add_column('quizzes', sa.Column('slide_content', sa.Text(), nullable=True))


def downgrade() -> None:
    """Remove slide_content column from quizzes table."""
    op.drop_column('quizzes', 'slide_content')
