"""Add provenance fields to policy documents

Revision ID: 20261011_0003
Revises: 20261010_0002
Create Date: 2026-10-11 03:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20261011_0003'
down_revision: Union[str, None] = '20261010_0002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('policy_documents', sa.Column('source_id', sa.String(length=50), nullable=True))
    op.add_column('policy_documents', sa.Column('canonical_url', sa.String(length=1024), nullable=True))
    op.add_column('policy_documents', sa.Column('content_hash', sa.String(length=64), nullable=True))
    op.create_index('ix_policy_documents_source_id', 'policy_documents', ['source_id'])


def downgrade() -> None:
    op.drop_index('ix_policy_documents_source_id', table_name='policy_documents')
    op.drop_column('policy_documents', 'content_hash')
    op.drop_column('policy_documents', 'canonical_url')
    op.drop_column('policy_documents', 'source_id')
