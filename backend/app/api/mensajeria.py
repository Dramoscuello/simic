from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from datetime import datetime
import logging
from app.database.config import get_db
from app.models.mensajeria import Conversacion, Mensaje
from app.models.notificacion import Notificacion
from app.models.usuario import Usuario
from app.models.rol import Rol
from app.models.sede import Sede
from app.api.deps import get_current_active_user
from app.core.redis_config import set_chat_viewing, is_viewing_chat
from pydantic import BaseModel

router = APIRouter(
    prefix="/mensajeria",
    tags=["mensajeria"]
)

logger = logging.getLogger(__name__)

# --- Schemas ---

class MensajeCreate(BaseModel):
    conversacion_id: Optional[int] = None
    destinatario_id: Optional[int] = None
    tipo: str = "texto"
    contenido: Optional[str] = None
    imagen_adjunto: Optional[str] = None  # base64

class ConversacionResponse(BaseModel):
    id: int
    institucion_id: int
    otro_participante_id: int
    otro_participante_nombre: str
    otro_participante_rol: str
    otro_participante_sede: Optional[str] = None
    asunto: Optional[str]
    estado: str
    ultimo_mensaje_at: datetime
    ultimo_mensaje: Optional[str]
    mensajes_nuevos: int = 0
    
    class Config:
        from_attributes = True

class MensajeResponse(BaseModel):
    id: int
    remitente_id: int
    remitente_nombre: str
    remitente_rol: str
    tipo: str
    contenido: Optional[str]
    imagen_adjunto: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class UsuarioDisponibleResponse(BaseModel):
    id: int
    nombre: str
    email: Optional[str]
    rol: str
    sede_nombre: Optional[str] = None

# --- Helpers ---

def _is_admin_or_docente(user: Usuario) -> bool:
    return user.rol.nombre in ("admin", "docente")

def _extract_conversacion_id(payload_json: Optional[dict]) -> Optional[int]:
    if not isinstance(payload_json, dict):
        return None
    try:
        return int(payload_json.get("conversacion_id", 0))
    except (TypeError, ValueError):
        return None

# --- Endpoints ---

@router.get("/usuarios-disponibles", response_model=List[UsuarioDisponibleResponse])
def get_usuarios_disponibles(
    q: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user),
):
    if not _is_admin_or_docente(current_user):
        raise HTTPException(status_code=403, detail="No autorizado")

    query = (
        db.query(Usuario)
        .join(Rol, Rol.id == Usuario.rol_id)
        .outerjoin(Sede, Sede.id == Usuario.sede_id)
        .filter(
            Usuario.institucion_id == current_user.institucion_id,
            Usuario.id != current_user.id,
            Rol.nombre.in_(["admin", "docente"]),
            Usuario.activo == True,
        )
    )

    if q:
        like = f"%{q}%"
        query = query.filter(Usuario.nombre.ilike(like) | Usuario.email.ilike(like))

    users = query.order_by(Usuario.nombre.asc()).all()

    return [
        UsuarioDisponibleResponse(
            id=u.id,
            nombre=u.nombre,
            email=u.email,
            rol=u.rol.nombre if u.rol else "N/A",
            sede_nombre=u.sede.nombre if u.sede else None,
        )
        for u in users
    ]


@router.get("/conversaciones", response_model=List[ConversacionResponse])
def get_conversaciones(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user),
):
    if not _is_admin_or_docente(current_user):
        raise HTTPException(status_code=403, detail="No autorizado")

    query = db.query(Conversacion).filter(
        (Conversacion.participante_1_id == current_user.id)
        | (Conversacion.participante_2_id == current_user.id)
    )

    conversaciones = query.order_by(Conversacion.ultimo_mensaje_at.desc()).all()

    # Unread counts
    mensajes_nuevos_por_chat: dict[int, int] = {}
    conversaciones_ids = [c.id for c in conversaciones]
    if conversaciones_ids:
        allowed_ids = set(conversaciones_ids)
        notificaciones = db.query(Notificacion).filter(
            Notificacion.usuario_id == current_user.id,
            Notificacion.tipo == "MENSAJE_NUEVO",
            Notificacion.leida.is_(False),
        ).all()

        for notif in notificaciones:
            conv_id = _extract_conversacion_id(notif.payload_json)
            if conv_id and conv_id in allowed_ids:
                count = int((notif.payload_json or {}).get("unread_messages_count", 1))
                mensajes_nuevos_por_chat[conv_id] = mensajes_nuevos_por_chat.get(conv_id, 0) + max(count, 1)

    # Load participants for all conversations
    participant_ids = set()
    for c in conversaciones:
        if c.participante_1_id:
            participant_ids.add(c.participante_1_id)
        if c.participante_2_id:
            participant_ids.add(c.participante_2_id)

    users_map: dict[int, Usuario] = {}
    if participant_ids:
        users_list = (
            db.query(Usuario)
            .options(joinedload(Usuario.rol), joinedload(Usuario.sede))
            .filter(Usuario.id.in_(participant_ids))
            .all()
        )
        users_map = {u.id: u for u in users_list}

    result = []
    for c in conversaciones:
        other_id = (
            c.participante_2_id if c.participante_1_id == current_user.id else c.participante_1_id
        )
        other_user = users_map.get(other_id) if other_id else None

        last_msg = c.mensajes[-1].contenido if c.mensajes else "Nueva conversación"

        result.append({
            "id": c.id,
            "institucion_id": c.institucion_id,
            "otro_participante_id": other_id or 0,
            "otro_participante_nombre": other_user.nombre if other_user else "Desconocido",
            "otro_participante_rol": other_user.rol.nombre if other_user and other_user.rol else "N/A",
            "otro_participante_sede": other_user.sede.nombre if other_user and other_user.sede else None,
            "asunto": c.asunto,
            "estado": c.estado,
            "ultimo_mensaje_at": c.ultimo_mensaje_at,
            "ultimo_mensaje": last_msg,
            "mensajes_nuevos": mensajes_nuevos_por_chat.get(c.id, 0),
        })
    return result


@router.get("/conversaciones/{conversacion_id}/mensajes", response_model=List[MensajeResponse])
def get_mensajes(
    conversacion_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user),
):
    conversacion = db.query(Conversacion).get(conversacion_id)
    if not conversacion:
        raise HTTPException(status_code=404, detail="Conversación no encontrada")

    if current_user.id not in (conversacion.participante_1_id, conversacion.participante_2_id):
        raise HTTPException(status_code=403, detail="No tiene acceso a este chat")

    mensajes = (
        db.query(Mensaje)
        .options(joinedload(Mensaje.remitente).joinedload(Usuario.rol))
        .filter(Mensaje.conversacion_id == conversacion_id)
        .order_by(Mensaje.created_at.asc())
        .all()
    )

    return [
        MensajeResponse(
            id=m.id,
            remitente_id=m.remitente_id,
            remitente_nombre=m.remitente.nombre if m.remitente else "Usuario Eliminado",
            remitente_rol=m.remitente.rol.nombre if m.remitente and m.remitente.rol else "N/A",
            tipo=m.tipo,
            contenido=m.contenido,
            imagen_adjunto=m.imagen_adjunto,
            created_at=m.created_at,
        )
        for m in mensajes
    ]


@router.post("/conversaciones/{conversacion_id}/ping")
def ping_conversacion(
    conversacion_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user),
):
    conversacion = db.query(Conversacion).get(conversacion_id)
    if not conversacion:
        raise HTTPException(status_code=404, detail="Conversación no encontrada")

    if current_user.id not in (conversacion.participante_1_id, conversacion.participante_2_id):
        raise HTTPException(status_code=403, detail="No tiene acceso a este chat")

    set_chat_viewing(current_user.id, conversacion_id)
    return {"status": "ok"}


@router.post("/conversaciones/{conversacion_id}/marcar-nuevos-como-leidos")
def marcar_nuevos_como_leidos(
    conversacion_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user),
):
    if not _is_admin_or_docente(current_user):
        raise HTTPException(status_code=403, detail="No autorizado")

    conversacion = db.query(Conversacion).get(conversacion_id)
    if not conversacion:
        raise HTTPException(status_code=404, detail="Conversación no encontrada")

    if current_user.id not in (conversacion.participante_1_id, conversacion.participante_2_id):
        raise HTTPException(status_code=403, detail="No tiene acceso a este chat")

    notificaciones = db.query(Notificacion).filter(
        Notificacion.usuario_id == current_user.id,
        Notificacion.tipo == "MENSAJE_NUEVO",
        Notificacion.leida.is_(False),
    ).all()

    ids_to_update: list[int] = []
    for notif in notificaciones:
        notif_conv_id = _extract_conversacion_id(notif.payload_json)
        if notif_conv_id == conversacion_id:
            ids_to_update.append(notif.id)

    if ids_to_update:
        db.query(Notificacion).filter(Notificacion.id.in_(ids_to_update)).update(
            {"leida": True, "leida_at": datetime.now()},
            synchronize_session=False,
        )
        db.commit()

    return {"updated_count": len(ids_to_update)}


@router.post("/enviar", response_model=MensajeResponse)
def enviar_mensaje(
    msg_in: MensajeCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user),
):
    if not _is_admin_or_docente(current_user):
        raise HTTPException(status_code=403, detail="No autorizado")

    conversacion = None

    if msg_in.conversacion_id:
        conversacion = db.query(Conversacion).get(msg_in.conversacion_id)
        if not conversacion:
            raise HTTPException(status_code=404, detail="Conversación no encontrada")

        if current_user.id not in (conversacion.participante_1_id, conversacion.participante_2_id):
            raise HTTPException(status_code=403, detail="No autorizado")

        if conversacion.estado == "cerrada":
            raise HTTPException(status_code=409, detail="Esta conversación está finalizada")

    elif msg_in.destinatario_id:
        destinatario = db.query(Usuario).filter(
            Usuario.id == msg_in.destinatario_id,
            Usuario.institucion_id == current_user.institucion_id,
            Usuario.activo == True,
        ).first()
        if not destinatario:
            raise HTTPException(status_code=400, detail="Destinatario no encontrado o no pertenece a tu institución")

        existing = (
            db.query(Conversacion)
            .filter(
                Conversacion.institucion_id == current_user.institucion_id,
                Conversacion.estado == "abierta",
                (
                    (Conversacion.participante_1_id == current_user.id)
                    & (Conversacion.participante_2_id == destinatario.id)
                )
                | (
                    (Conversacion.participante_1_id == destinatario.id)
                    & (Conversacion.participante_2_id == current_user.id)
                ),
            )
            .first()
        )

        if existing:
            conversacion = existing
        else:
            p1, p2 = sorted([current_user.id, destinatario.id])
            conversacion = Conversacion(
                institucion_id=current_user.institucion_id,
                participante_1_id=p1,
                participante_2_id=p2,
                asunto="Conversación directa",
                estado="abierta",
            )
            db.add(conversacion)
            db.commit()
            db.refresh(conversacion)
    else:
        raise HTTPException(status_code=400, detail="Se requiere conversacion_id o destinatario_id")

    nuevo_msg = Mensaje(
        conversacion_id=conversacion.id,
        remitente_id=current_user.id,
        tipo="texto",
        contenido=msg_in.contenido,
        imagen_adjunto=msg_in.imagen_adjunto,
    )
    db.add(nuevo_msg)
    db.flush()

    conversacion.ultimo_mensaje_at = datetime.now()

    # Notifications — fire-and-forget, never roll back the message
    try:
        other_id = (
            conversacion.participante_2_id
            if conversacion.participante_1_id == current_user.id
            else conversacion.participante_1_id
        )

        if other_id and not is_viewing_chat(other_id, conversacion.id):
            event_key = f"msg:{conversacion.id}:{nuevo_msg.id}"

            existing_notif = (
                db.query(Notificacion)
                .filter(
                    Notificacion.usuario_id == other_id,
                    Notificacion.tipo == "MENSAJE_NUEVO",
                    Notificacion.leida.is_(False),
                )
                .first()
            )

            if existing_notif:
                conv_id_in_notif = _extract_conversacion_id(existing_notif.payload_json)
                if conv_id_in_notif == conversacion.id:
                    payload = dict(existing_notif.payload_json or {})
                    payload["unread_messages_count"] = int(payload.get("unread_messages_count", 1)) + 1
                    existing_notif.payload_json = payload
                else:
                    db.add(Notificacion(
                        usuario_id=other_id,
                        institucion_id=current_user.institucion_id,
                        tipo="MENSAJE_NUEVO",
                        titulo="Nuevo mensaje",
                        mensaje=f"{current_user.nombre}: {msg_in.contenido[:80] if msg_in.contenido else ''}",
                        payload_json={
                            "conversacion_id": conversacion.id,
                            "unread_messages_count": 1,
                            "actor_nombre": current_user.nombre,
                        },
                        actor_usuario_id=current_user.id,
                        event_key=event_key,
                    ))
            else:
                db.add(Notificacion(
                    usuario_id=other_id,
                    institucion_id=current_user.institucion_id,
                    tipo="MENSAJE_NUEVO",
                    titulo="Nuevo mensaje",
                    mensaje=f"{current_user.nombre}: {msg_in.contenido[:80] if msg_in.contenido else ''}",
                    payload_json={
                        "conversacion_id": conversacion.id,
                        "unread_messages_count": 1,
                        "actor_nombre": current_user.nombre,
                    },
                    actor_usuario_id=current_user.id,
                    event_key=event_key,
                ))
    except Exception:
        pass

    db.commit()
    db.refresh(nuevo_msg)

    return MensajeResponse(
        id=nuevo_msg.id,
        remitente_id=nuevo_msg.remitente_id,
        remitente_nombre=current_user.nombre,
        remitente_rol=current_user.rol.nombre if current_user.rol else "N/A",
        tipo=nuevo_msg.tipo,
        contenido=nuevo_msg.contenido,
        imagen_adjunto=nuevo_msg.imagen_adjunto,
        created_at=nuevo_msg.created_at,
    )
