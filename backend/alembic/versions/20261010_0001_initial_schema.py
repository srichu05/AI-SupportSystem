"""Initial schema for Complaint Response Assistant

Revision ID: 20261010_0001
Revises: 
Create Date: 2026-10-10 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision: str = '20261010_0001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Enable pgvector extension on PostgreSQL
    conn = op.get_bind()
    if conn.dialect.name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    # 2. Table: policy_documents
    op.create_table(
        'policy_documents',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('source_filename', sa.String(length=255), nullable=False),
        sa.Column('storage_path', sa.String(length=1024), nullable=True),
        sa.Column('document_type', sa.String(length=20), nullable=False),
        sa.Column('version_label', sa.String(length=50), nullable=True),
        sa.Column('effective_from', sa.Date(), nullable=True),
        sa.Column('effective_to', sa.Date(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # 3. Table: policy_chunks
    op.create_table(
        'policy_chunks',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('document_id', sa.UUID(), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('section_path', sa.String(length=512), nullable=True),
        sa.Column('page_number', sa.Integer(), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('embedding', Vector(768), nullable=True),
        sa.Column('embedding_model', sa.String(length=100), nullable=True),
        sa.Column('content_hash', sa.String(length=64), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['policy_documents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('document_id', 'chunk_index', name='uq_policy_chunk_doc_index')
    )
    op.create_index('ix_policy_chunks_document_id', 'policy_chunks', ['document_id'])

    # GIN index for PostgreSQL full-text search
    if conn.dialect.name == "postgresql":
        op.execute(
            "CREATE INDEX IF NOT EXISTS ix_policy_chunks_content_tsvector "
            "ON policy_chunks USING gin (to_tsvector('english', content));"
        )

    # 4. Table: complaints
    op.create_table(
        'complaints',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('complaint_text', sa.Text(), nullable=False),
        sa.Column('response_tone', sa.String(length=50), nullable=False, server_default='professional'),
        sa.Column('processing_status', sa.String(length=50), nullable=False, server_default='received'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # 5. Table: complaint_issues
    op.create_table(
        'complaint_issues',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('complaint_id', sa.UUID(), nullable=False),
        sa.Column('issue_text', sa.Text(), nullable=False),
        sa.Column('requested_resolution', sa.Text(), nullable=True),
        sa.Column('customer_facts', sa.JSON(), nullable=True),
        sa.Column('missing_facts', sa.JSON(), nullable=True),
        sa.Column('assessment_status', sa.String(length=50), nullable=False, server_default='needs_human_review'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['complaint_id'], ['complaints.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_complaint_issues_complaint_id', 'complaint_issues', ['complaint_id'])

    # 6. Table: issue_evidence
    op.create_table(
        'issue_evidence',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('issue_id', sa.UUID(), nullable=False),
        sa.Column('chunk_id', sa.UUID(), nullable=False),
        sa.Column('retrieval_source', sa.String(length=50), nullable=False),
        sa.Column('retrieval_rank', sa.Integer(), nullable=True),
        sa.Column('fusion_score', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['issue_id'], ['complaint_issues.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['chunk_id'], ['policy_chunks.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_issue_evidence_issue_id', 'issue_evidence', ['issue_id'])
    op.create_index('ix_issue_evidence_chunk_id', 'issue_evidence', ['chunk_id'])

    # 7. Table: response_drafts
    op.create_table(
        'response_drafts',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('complaint_id', sa.UUID(), nullable=False),
        sa.Column('draft_text', sa.Text(), nullable=False),
        sa.Column('structured_output', sa.JSON(), nullable=True),
        sa.Column('validation_status', sa.String(length=50), nullable=False, server_default='valid'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['complaint_id'], ['complaints.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_response_drafts_complaint_id', 'response_drafts', ['complaint_id'])

    # 8. Table: review_decisions
    op.create_table(
        'review_decisions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('complaint_id', sa.UUID(), nullable=False),
        sa.Column('draft_id', sa.UUID(), nullable=False),
        sa.Column('decision', sa.String(length=50), nullable=False),
        sa.Column('final_response_text', sa.Text(), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('reviewer_id', sa.String(length=100), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['complaint_id'], ['complaints.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['draft_id'], ['response_drafts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_review_decisions_complaint_id', 'review_decisions', ['complaint_id'])
    op.create_index('ix_review_decisions_draft_id', 'review_decisions', ['draft_id'])


def downgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == "postgresql":
        op.execute("DROP INDEX IF EXISTS ix_policy_chunks_content_tsvector;")

    op.drop_table('review_decisions')
    op.drop_table('response_drafts')
    op.drop_table('issue_evidence')
    op.drop_table('complaint_issues')
    op.drop_table('complaints')
    op.drop_table('policy_chunks')
    op.drop_table('policy_documents')
