"""add current agents tracking to startup marketing data

Revision ID: d4f1a8c9b6e2
Revises: 961ad369abd8
Create Date: 2026-11-24 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy.dialects import postgresql
import sqlalchemy as sa

revision: str = 'd4f1a8c9b6e2'
down_revision: Union[str, Sequence[str], None] = '961ad369abd8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'startup_marketing_data',
        sa.Column(
            'current_agents',
            postgresql.JSON(astext_type=sa.Text()),
            nullable=True,
        ),
    )
    op.add_column('publishing_jobs', sa.Column('platform_account_id', sa.String(length=255), nullable=True))
    op.add_column('publishing_jobs', sa.Column('connection_status', sa.String(length=50), nullable=True))
    op.add_column(
        'publishing_jobs',
        sa.Column(
            'publishing_scopes',
            postgresql.JSON(astext_type=sa.Text()),
            nullable=True,
        ),
    )
    op.add_column('publishing_jobs', sa.Column('token_expires_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column('publishing_jobs', 'token_expires_at')
    op.drop_column('publishing_jobs', 'publishing_scopes')
    op.drop_column('publishing_jobs', 'connection_status')
    op.drop_column('publishing_jobs', 'platform_account_id')
    op.drop_column('startup_marketing_data', 'current_agents')
