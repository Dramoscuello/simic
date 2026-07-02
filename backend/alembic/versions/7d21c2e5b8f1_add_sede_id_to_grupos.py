"""add_sede_id_to_grupos

Revision ID: 7d21c2e5b8f1
Revises: d2234f059d34
Create Date: 2026-06-27 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector


# revision identifiers, used by Alembic.
revision = '7d21c2e5b8f1'
down_revision = 'd2234f059d34'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    columns = [c['name'] for c in inspector.get_columns('grupos')]

    if 'sede_id' not in columns:
        op.add_column('grupos', sa.Column('sede_id', sa.Integer(), nullable=True))
        op.create_foreign_key(None, 'grupos', 'sedes', ['sede_id'], ['id'])

    conn.execute(sa.text("""
        UPDATE grupos g
        SET sede_id = (
            SELECT s.id FROM sedes s
            WHERE s.institucion_id = g.institucion_id AND s.activo = true
            ORDER BY s.id
            LIMIT 1
        )
        WHERE g.sede_id IS NULL
    """))


def downgrade() -> None:
    op.drop_constraint(None, 'grupos', type_='foreignkey')
    op.drop_column('grupos', 'sede_id')
