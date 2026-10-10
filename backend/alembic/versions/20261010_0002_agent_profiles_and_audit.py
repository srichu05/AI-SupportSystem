"""Add agent profiles, role accountability, and complaint audit logging

Revision ID: 20261010_0002
Revises: 20261010_0001
Create Date: 2026-10-10 19:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20261010_0002'
down_revision: Union[str, None] = '20261010_0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Table: agent_profiles
    op.create_table(
        'agent_profiles',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('clerk_user_id', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('display_name', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False, server_default='support_agent'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('clerk_user_id', name='uq_agent_profiles_clerk_user_id'),
    )
    op.create_index('ix_agent_profiles_clerk_user_id', 'agent_profiles', ['clerk_user_id'])
    op.create_index('ix_agent_profiles_email', 'agent_profiles', ['email'])

    # 2. Table: complaint_audit_logs
    op.create_table(
        'complaint_audit_logs',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('complaint_id', sa.UUID(), nullable=False),
        sa.Column('actor_agent_id', sa.UUID(), nullable=True),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['complaint_id'], ['complaints.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['actor_agent_id'], ['agent_profiles.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_complaint_audit_logs_complaint_id', 'complaint_audit_logs', ['complaint_id'])
    op.create_index('ix_complaint_audit_logs_actor_agent_id', 'complaint_audit_logs', ['actor_agent_id'])
    op.create_index('ix_complaint_audit_logs_event_type', 'complaint_audit_logs', ['event_type'])

    # 3. Add ownership columns to complaints
    op.add_column('complaints', sa.Column('created_by_agent_id', sa.UUID(), nullable=True))
    op.add_column('complaints', sa.Column('assigned_to_agent_id', sa.UUID(), nullable=True))
    op.create_foreign_key(
        'fk_complaints_created_by_agent',
        'complaints',
        'agent_profiles',
        ['created_by_agent_id'],
        ['id'],
        ondelete='SET NULL',
    )
    op.create_foreign_key(
        'fk_complaints_assigned_to_agent',
        'complaints',
        'agent_profiles',
        ['assigned_to_agent_id'],
        ['id'],
        ondelete='SET NULL',
    )
    op.create_index('ix_complaints_created_by_agent_id', 'complaints', ['created_by_agent_id'])
    op.create_index('ix_complaints_assigned_to_agent_id', 'complaints', ['assigned_to_agent_id'])

    # 4. Add created_by_agent_id to response_drafts
    op.add_column('response_drafts', sa.Column('created_by_agent_id', sa.UUID(), nullable=True))
    op.create_foreign_key(
        'fk_response_drafts_created_by_agent',
        'response_drafts',
        'agent_profiles',
        ['created_by_agent_id'],
        ['id'],
        ondelete='SET NULL',
    )
    op.create_index('ix_response_drafts_created_by_agent_id', 'response_drafts', ['created_by_agent_id'])

    # 5. Add reviewer_profile_id to review_decisions
    op.add_column('review_decisions', sa.Column('reviewer_profile_id', sa.UUID(), nullable=True))
    op.create_foreign_key(
        'fk_review_decisions_reviewer_profile',
        'review_decisions',
        'agent_profiles',
        ['reviewer_profile_id'],
        ['id'],
        ondelete='SET NULL',
    )
    op.create_index('ix_review_decisions_reviewer_profile_id', 'review_decisions', ['reviewer_profile_id'])


def downgrade() -> None:
    # 5. Drop review_decisions additions
    op.drop_index('ix_review_decisions_reviewer_profile_id', table_name='review_decisions')
    op.drop_constraint('fk_review_decisions_reviewer_profile', 'review_decisions', type_='foreignkey')
    op.drop_column('review_decisions', 'reviewer_profile_id')

    # 4. Drop response_drafts additions
    op.drop_index('ix_response_drafts_created_by_agent_id', table_name='response_drafts')
    op.drop_constraint('fk_response_drafts_created_by_agent', 'response_drafts', type_='foreignkey')
    op.drop_column('response_drafts', 'created_by_agent_id')

    # 3. Drop complaints additions
    op.drop_index('ix_complaints_assigned_to_agent_id', table_name='complaints')
    op.drop_index('ix_complaints_created_by_agent_id', table_name='complaints')
    op.drop_constraint('fk_complaints_assigned_to_agent', 'complaints', type_='foreignkey')
    op.drop_constraint('fk_complaints_created_by_agent', 'complaints', type_='foreignkey')
    op.drop_column('complaints', 'assigned_to_agent_id')
    op.drop_column('complaints', 'created_by_agent_id')

    # 2. Drop complaint_audit_logs
    op.drop_index('ix_complaint_audit_logs_event_type', table_name='complaint_audit_logs')
    op.drop_index('ix_complaint_audit_logs_actor_agent_id', table_name='complaint_audit_logs')
    op.drop_index('ix_complaint_audit_logs_complaint_id', table_name='complaint_audit_logs')
    op.drop_table('complaint_audit_logs')

    # 1. Drop agent_profiles
    op.drop_index('ix_agent_profiles_email', table_name='agent_profiles')
    op.drop_index('ix_agent_profiles_clerk_user_id', table_name='agent_profiles')
    op.drop_table('agent_profiles')
