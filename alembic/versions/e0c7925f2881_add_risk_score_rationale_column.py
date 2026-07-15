"""add risk score rationale column

Revision ID: e0c7925f2881
Revises: 1fe857b88c41
Create Date: 2026-07-17 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e0c7925f2881'
down_revision: Union[str, Sequence[str], None] = '1fe857b88c41'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('risk_scores', sa.Column('rationale', sa.Text(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('risk_scores', 'rationale')
