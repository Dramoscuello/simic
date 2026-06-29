from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user
from app.database.config import get_db
from app.models.notificacion import Notificacion
from app.models.usuario import Usuario
from app.schemas.notificacion import MarkAllReadOut, NotificacionOut, UnreadCountOut


router = APIRouter(prefix="/notificaciones", tags=["notificaciones"])

ALLOWED_ROLES = {'admin', 'docente'}


def _ensure_notifications_access(current_user: Usuario) -> None:
    role_name = current_user.rol.nombre if current_user.rol else None
    if role_name not in ALLOWED_ROLES:
        raise HTTPException(status_code=403, detail="No autorizado")


@router.get("/", response_model=List[NotificacionOut])
def list_notifications(
    include_read: bool = Query(default=False),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user),
):
    _ensure_notifications_access(current_user)

    try:
        query = db.query(Notificacion).filter(Notificacion.usuario_id == current_user.id)
        if not include_read:
            query = query.filter(Notificacion.leida.is_(False))

        # DEBUG LOGS
        total_matches = query.count()
        results = query.order_by(Notificacion.created_at.desc()).offset(offset).limit(limit).all()
        print(f"DEBUG NO-NOTIFS: user={current_user.id} role={current_user.rol.nombre} total_query={total_matches} returning={len(results)}")
        
        return results
    except Exception as e:
        import traceback
        print(f"ERROR list_notifications: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error interno obteniendo notificaciones: {str(e)}")


@router.get("/unread-count", response_model=UnreadCountOut)
def get_unread_count(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user),
):
    _ensure_notifications_access(current_user)
    unread_count = (
        db.query(Notificacion)
        .filter(
            Notificacion.usuario_id == current_user.id,
            Notificacion.leida.is_(False),
        )
        .count()
    )
    return {"unread_count": unread_count}


@router.patch("/{notification_id}/read", response_model=NotificacionOut)
def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user),
):
    _ensure_notifications_access(current_user)

    notification = (
        db.query(Notificacion)
        .filter(
            Notificacion.id == notification_id,
            Notificacion.usuario_id == current_user.id,
        )
        .first()
    )
    if not notification:
        raise HTTPException(status_code=404, detail="Notificación no encontrada")

    if not notification.leida:
        notification.leida = True
        notification.leida_at = datetime.now(timezone.utc)
        db.add(notification)
        db.commit()
        db.refresh(notification)

    return notification


@router.post("/read-all", response_model=MarkAllReadOut)
def mark_all_notifications_read(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user),
):
    _ensure_notifications_access(current_user)

    now_utc = datetime.now(timezone.utc)
    updated_count = (
        db.query(Notificacion)
        .filter(
            Notificacion.usuario_id == current_user.id,
            Notificacion.leida.is_(False),
        )
        .update(
            {
                Notificacion.leida: True,
                Notificacion.leida_at: now_utc,
            },
            synchronize_session=False,
        )
    )
    db.commit()
    return {"updated_count": updated_count}
