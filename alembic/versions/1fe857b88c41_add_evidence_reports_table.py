"""add evidence_reports table

Revision ID: 1fe857b88c41
Revises: abb1ae520e2d
Create Date: 2026-07-16 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '1fe857b88c41'
down_revision: Union[str, Sequence[str], None] = 'abb1ae520e2d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'evidence_reports',
        sa.Column('case_id', sa.Uuid(), nullable=False),
        sa.Column(
            'submitted_evidence',
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), 'postgresql'),
            nullable=True,
        ),
        sa.Column(
            'gaps',
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), 'postgresql'),
            nullable=True,
        ),
        sa.Column('completeness_score', sa.Float(), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('(CURRENT_TIMESTAMP)'),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ['case_id'],
            ['cases.id'],
            name=op.f('fk_evidence_reports_case_id_cases'),
            ondelete='CASCADE',
        ),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_evidence_reports')),
    )
    op.create_index(
        op.f('ix_evidence_reports_case_id'), 'evidence_reports', ['case_id'], unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_evidence_reports_case_id'), table_name='evidence_reports')
    op.drop_table('evidence_reports')
