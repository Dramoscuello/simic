"""add_participantes_to_conversaciones

Revision ID: 9a4b5c6d7e8f
Revises: 8f3a2d7c1b9e
Create Date: 2026-06-27 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector


revision = '9a4b5c6d7e8f'
down_revision = '8f3a2d7c1b9e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    columns = [c['name'] for c in inspector.get_columns('conversaciones')]

    if 'participante_1_id' not in columns:
        op.add_column('conversaciones', sa.Column('participante_1_id', sa.Integer(), nullable=True))
        op.create_foreign_key(None, 'conversaciones', 'usuarios', ['participante_1_id'], ['id'])

    if 'participante_2_id' not in columns:
        op.add_column('conversaciones', sa.Column('participante_2_id', sa.Integer(), nullable=True))
        op.create_foreign_key(None, 'conversaciones', 'usuarios', ['participante_2_id'], ['id'])


def downgrade() -> None:
    op.drop_constraint(None, 'conversaciones', type_='foreignkey')
    op.drop_constraint(None, 'conversaciones', type_='foreignkey')
    op.drop_column('conversaciones', 'participante_2_id')
    op.drop_column('conversaciones', 'participante_1_id')
