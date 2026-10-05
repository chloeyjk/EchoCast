"""add users and preferences

Revision ID: c1a2f3e4d5b6
Revises: b557dbece17e
Create Date: 2026-10-05 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c1a2f3e4d5b6'
down_revision: Union[str, Sequence[str], None] = 'b557dbece17e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('username', sa.String(), nullable=False),
    sa.Column('hashed_password', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    op.create_table('preferences',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('topic', sa.String(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id']),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_preferences_id'), 'preferences', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_preferences_id'), table_name='preferences')
    op.drop_table('preferences')
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_table('users')
