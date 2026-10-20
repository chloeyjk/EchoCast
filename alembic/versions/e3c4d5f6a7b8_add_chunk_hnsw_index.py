"""add hnsw index on chunks.embedding

Revision ID: e3c4d5f6a7b8
Revises: d2b3c4e5f6a7
Create Date: 2026-10-20 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = 'e3c4d5f6a7b8'
down_revision: Union[str, Sequence[str], None] = 'd2b3c4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

INDEX_NAME = 'ix_chunks_embedding_hnsw'


def upgrade() -> None:
    if op.get_bind().dialect.name != 'postgresql':
        return
    op.execute(
        f"CREATE INDEX {INDEX_NAME} ON chunks "
        "USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64)"
    )


def downgrade() -> None:
    if op.get_bind().dialect.name != 'postgresql':
        return
    op.execute(f"DROP INDEX {INDEX_NAME}")
