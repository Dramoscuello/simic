import logging
from typing import Iterable, Optional

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.notificacion import Notificacion
from app.models.usuario import Usuario


logger = logging.getLogger(__name__)


class NotificacionTipo:
    MENSAJE_NUEVO = "mensaje_nuevo"


def get_admins_institucion(
    db: Session,
    institucion_id: int,
    exclude_user_id: Optional[int] = None,
) -> list[Usuario]:
    query = db.query(Usuario).filter(
        Usuario.institucion_id == institucion_id,
        Usuario.activo.is_(True),
        Usuario.rol.has(nombre="admin"),
    )
    if exclude_user_id:
        query = query.filter(Usuario.id != exclude_user_id)
    return query.all()


def get_admins(db: Session, exclude_user_id: Optional[int] = None) -> list[Usuario]:
    query = db.query(Usuario).filter(
        Usuario.activo.is_(True),
        Usuario.rol.has(nombre="admin"),
    )
    if exclude_user_id:
        query = query.filter(Usuario.id != exclude_user_id)
    return query.all()


def create_notifications_bulk(
    db: Session,
    *,
    recipients: Iterable[int],
    institucion_id: Optional[int],
    tipo: str,
    titulo: str,
    mensaje: str,
    payload_json: Optional[dict],
    actor_usuario_id: Optional[int],
    event_key: str,
) -> int:
    created = 0
    for usuario_id in recipients:
        try:
            # Savepoint por notificación: evita comprometer la transacción principal.
            with db.begin_nested():
                notification = Notificacion(
                    usuario_id=usuario_id,
                    institucion_id=institucion_id,
                    tipo=tipo,
                    titulo=titulo,
                    mensaje=mensaje,
                    payload_json=payload_json,
                    actor_usuario_id=actor_usuario_id,
                    event_key=event_key,
                )
                db.add(notification)
                db.flush()
                created += 1
        except IntegrityError:
            # Duplicado por (usuario_id, event_key). Es idempotente.
            logger.info(
                "Notificación duplicada ignorada",
                extra={"usuario_id": usuario_id, "event_key": event_key, "tipo": tipo},
            )
        except SQLAlchemyError:
            logger.exception(
                "Error creando notificación",
                extra={"usuario_id": usuario_id, "event_key": event_key, "tipo": tipo},
            )
    return created
