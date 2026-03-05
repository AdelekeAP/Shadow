"""add auth security columns to users

Revision ID: 6211460164fa
Revises: b7c2d4e91f06
Create Date: 2026-03-04 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '6211460164fa'
down_revision: Union[str, Sequence[str], None] = 'b7c2d4e91f06'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add auth security columns: failed_login_attempts, locked_until, token_version."""
    op.add_column('users', sa.Column('failed_login_attempts', sa.Integer(), nullable=True, server_default='0'))
    op.add_column('users', sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True))
    op.add_column('users', sa.Column('token_version', sa.Integer(), nullable=True, server_default='0'))


def downgrade() -> None:
    """Remove auth security columns."""
    op.drop_column('users', 'token_version')
    op.drop_column('users', 'locked_until')
    op.drop_column('users', 'failed_login_attempts')
