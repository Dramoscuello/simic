"""create_default_sedes

Revision ID: c28d1ada4dc1
Revises: 076ac924e65e
Create Date: 2026-06-26 09:42:56.383779

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c28d1ada4dc1'
down_revision = '076ac924e65e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Crear una sede "Sede Principal" para cada institución que aún no tenga sedes.
    op.execute(
        """
        INSERT INTO sedes (nombre, direccion, telefono, activo, institucion_id)
        SELECT 'Sede Principal', i.direccion, i.telefono, true, i.id
        FROM instituciones i
        WHERE NOT EXISTS (
            SELECT 1 FROM sedes s WHERE s.institucion_id = i.id
        )
        """
    )

    # Asignar a los simulacros sin sede la primera sede activa de su institución
    # (normalmente la sede principal recién creada).
    op.execute(
        """
        UPDATE simulacros sim
        SET sede_id = (
            SELECT MIN(s.id)
            FROM sedes s
            WHERE s.institucion_id = sim.institucion_id
              AND s.activo = true
        )
        WHERE sim.sede_id IS NULL
          AND sim.institucion_id IS NOT NULL
        """
    )


def downgrade() -> None:
    # Desvincular simulacros de las sedes principales creadas por esta migración
    # y luego eliminar esas sedes.
    op.execute(
        """
        UPDATE simulacros
        SET sede_id = NULL
        WHERE sede_id IN (
            SELECT id FROM sedes WHERE nombre = 'Sede Principal'
        )
        """
    )
    op.execute(
        """
        DELETE FROM sedes
        WHERE nombre = 'Sede Principal'
        """
    )
