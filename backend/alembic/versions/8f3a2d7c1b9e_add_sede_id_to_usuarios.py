"""add_sede_id_to_usuarios

Revision ID: 8f3a2d7c1b9e
Revises: 7d21c2e5b8f1
Create Date: 2026-06-27 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector


# revision identifiers, used by Alembic.
revision = '8f3a2d7c1b9e'
down_revision = '7d21c2e5b8f1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    columns = [c['name'] for c in inspector.get_columns('usuarios')]

    if 'sede_id' not in columns:
        op.add_column('usuarios', sa.Column('sede_id', sa.Integer(), nullable=True))
        op.create_foreign_key(None, 'usuarios', 'sedes', ['sede_id'], ['id'])


def downgrade() -> None:
    op.drop_constraint(None, 'usuarios', type_='foreignkey')
    op.drop_column('usuarios', 'sede_id')
