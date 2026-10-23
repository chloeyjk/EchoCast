"""replace article_summaries with citation-grounded claims

Revision ID: f4d5e6a7b8c9
Revises: e3c4d5f6a7b8
Create Date: 2026-10-23 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f4d5e6a7b8c9'
down_revision: Union[str, Sequence[str], None] = 'e3c4d5f6a7b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index(op.f('ix_article_summaries_id'), table_name='article_summaries')
    op.drop_table('article_summaries')

    op.create_table('summaries',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('topic', sa.String(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_summaries_id'), 'summaries', ['id'], unique=False)
    op.create_index(op.f('ix_summaries_topic'), 'summaries', ['topic'], unique=False)

    op.create_table('claims',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('summary_id', sa.Integer(), nullable=False),
    sa.Column('text', sa.Text(), nullable=False),
    sa.Column('source_chunk_id', sa.Integer(), nullable=False),
    sa.Column('position', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['summary_id'], ['summaries.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['source_chunk_id'], ['chunks.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_claims_id'), 'claims', ['id'], unique=False)
    op.create_index(op.f('ix_claims_summary_id'), 'claims', ['summary_id'], unique=False)
    op.create_index(op.f('ix_claims_source_chunk_id'), 'claims', ['source_chunk_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_claims_source_chunk_id'), table_name='claims')
    op.drop_index(op.f('ix_claims_summary_id'), table_name='claims')
    op.drop_index(op.f('ix_claims_id'), table_name='claims')
    op.drop_table('claims')
    op.drop_index(op.f('ix_summaries_topic'), table_name='summaries')
    op.drop_index(op.f('ix_summaries_id'), table_name='summaries')
    op.drop_table('summaries')

    op.create_table('article_summaries',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(), nullable=False),
    sa.Column('url', sa.String(), nullable=True),
    sa.Column('summary', sa.Text(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_article_summaries_id'), 'article_summaries', ['id'], unique=False)
