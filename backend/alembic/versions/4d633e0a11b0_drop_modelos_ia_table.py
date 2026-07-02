"""drop_modelos_ia_table

Revision ID: 4d633e0a11b0
Revises: ac4df0fec0b7
Create Date: 2026-06-26 19:55:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4d633e0a11b0'
down_revision = 'ac4df0fec0b7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_table('modelos_ia')


def downgrade() -> None:
    op.create_table(
        'modelos_ia',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nombre_visible', sa.String(length=255), nullable=False),
        sa.Column('modelo_codigo', sa.String(length=255), nullable=False),
        sa.Column('es_default', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
