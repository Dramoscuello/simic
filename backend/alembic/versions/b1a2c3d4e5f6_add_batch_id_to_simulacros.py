"""add_batch_id_to_simulacros

Revision ID: b1a2c3d4e5f6
Revises: 9a4b5c6d7e8f
Create Date: 2026-07-03 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector


revision = 'b1a2c3d4e5f6'
down_revision = '9a4b5c6d7e8f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    columns = [c['name'] for c in inspector.get_columns('simulacros')]

    if 'batch_id' not in columns:
        op.add_column('simulacros', sa.Column('batch_id', sa.String(100), nullable=True))
        op.create_index('ix_simulacros_batch_id', 'simulacros', ['batch_id'])


def downgrade() -> None:
    op.drop_index('ix_simulacros_batch_id', 'simulacros')
    op.drop_column('simulacros', 'batch_id')
