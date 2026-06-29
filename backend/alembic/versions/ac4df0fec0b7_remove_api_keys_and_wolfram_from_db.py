"""remove_api_keys_and_wolfram_from_db

Revision ID: ac4df0fec0b7
Revises: c28d1ada4dc1
Create Date: 2026-06-26 19:18:11.879395

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ac4df0fec0b7'
down_revision = 'c28d1ada4dc1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column('modelos_ia', 'api_key')
    op.drop_column('instituciones', 'wolfram_app_id')


def downgrade() -> None:
    op.add_column('modelos_ia', sa.Column('api_key', sa.String(length=512), nullable=True))
    op.add_column('instituciones', sa.Column('wolfram_app_id', sa.String(length=255), nullable=True))
