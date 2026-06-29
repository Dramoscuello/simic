import os
from fastapi import Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone

from app.api.deps import get_current_active_user
from app.database.config import get_db
from app.models.simulacro import Simulacro
from app.models.respuesta_estudiante import RespuestaEstudiante
from app.models.usuario import Usuario
from app.schemas.respuesta_estudiante import (
    RespuestaEstudianteResponse,
    RespuestaEstudianteUpdate,
    RespuestaEstudianteFinalize
)
from app.services.analisis_service import AnalisisService
from app.core.redis_config import get_redis

from app.api.simulacros_router import router

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
MARGEN_TOLERANCIA_MIN = int(os.getenv("SIMULACRO_MARGIN_MINUTES", "5"))
MIN_FINISH_PCT = float(os.getenv("SIMULACRO_MIN_FINISH_PCT", "0.30"))

def _now_utc() -> datetime:
    return datetime.now(timezone.utc)

def _ensure_aware(dt: datetime) -> datetime:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt

def _calcular_limite(fecha_inicio: datetime, duracion_minutos: int) -> datetime:
    if not fecha_inicio or not duracion_minutos:
        return None
    return fecha_inicio + timedelta(minutes=duracion_minutos + MARGEN_TOLERANCIA_MIN)

def _calcular_minimo(fecha_inicio: datetime, duracion_minutos: int) -> datetime:
    if not fecha_inicio or not duracion_minutos:
        return None
    total_seconds = max(0, int(duracion_minutos * 60))
    min_seconds = max(0, int(total_seconds * MIN_FINISH_PCT))
    return fecha_inicio + timedelta(seconds=min_seconds)

def _calcular_resultados(contenido: dict, respuestas_finales: dict):
    preguntas = contenido.get("preguntas", [])
    mapa_preguntas = {str(p.get("id")): p for p in preguntas}
    total_correctas = 0
    total_incorrectas = 0
    respuestas_detalladas = {}

    for preg_id, resp_usuario in respuestas_finales.items():
        pregunta_config = mapa_preguntas.get(str(preg_id))

        detalles = {
            "respuesta_usuario": resp_usuario,
            "es_correcta": False
        }

        if pregunta_config:
            correcta = pregunta_config.get("respuesta_correcta")
            es_correcta = (resp_usuario == correcta)

            detalles["respuesta_correcta"] = correcta
            detalles["es_correcta"] = es_correcta

            # Copiar metadatos
            for meta in ["competencia", "componente", "tema", "dificultad"]:
                if meta in pregunta_config:
                    detalles[meta] = pregunta_config[meta]

            if es_correcta:
                total_correctas += 1
            else:
                total_incorrectas += 1

        respuestas_detalladas[preg_id] = detalles

    total_preguntas = len(preguntas)
    puntaje = 0.0
    if total_preguntas > 0:
        puntaje = (total_correctas / total_preguntas) * 100.0

    return respuestas_detalladas, total_correctas, total_incorrectas, puntaje

# -----------------------------------------------------------------------------
# 1. INICIAR SIMULACRO (CHECK-IN)
# -----------------------------------------------------------------------------
@router.post("/{simulacro_id}/iniciar", response_model=RespuestaEstudianteResponse)
def iniciar_simulacro(
    simulacro_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    db_simulacro = (
        db.query(Simulacro)
        .filter(Simulacro.id == simulacro_id)
        .with_for_update()
        .first()
    )
    if not db_simulacro:
        raise HTTPException(status_code=404, detail="Simulacro no encontrado")

    if not db_simulacro.activo and current_user.rol.nombre == "estudiante":
        raise HTTPException(status_code=403, detail="El simulacro no está activo para estudiantes")

    intento = db.query(RespuestaEstudiante).filter(
        RespuestaEstudiante.simulacro_id == simulacro_id,
        RespuestaEstudiante.usuario_id == current_user.id,
        RespuestaEstudiante.anulado.is_(False)
    ).first()

    if intento:
        if intento.fecha_finalizacion:
            raise HTTPException(status_code=400, detail="Ya has finalizado este simulacro. No se permiten reintentos.")

        if not intento.fecha_inicio:
            intento.fecha_inicio = _now_utc()
            db.commit()
            db.refresh(intento)

        fecha_inicio = _ensure_aware(intento.fecha_inicio)
        limite = _calcular_limite(fecha_inicio, db_simulacro.duracion_minutos)
        if limite and _now_utc() > limite:
            raise HTTPException(status_code=400, detail="El tiempo para este simulacro ha expirado.")

        return intento

    nuevo_intento = RespuestaEstudiante(
        simulacro_id=simulacro_id,
        usuario_id=current_user.id,
        institucion_id=current_user.institucion_id if current_user.institucion_id else 1,
        respuestas={},
        respuestas_detalladas={},
        total_correctas=0,
        total_incorrectas=0,
        puntaje_total=None,
        tiempo_empleado=0,
        fecha_inicio=_now_utc(),
        fecha_finalizacion=None
    )

    db.add(nuevo_intento)
    db.commit()
    db.refresh(nuevo_intento)
    return nuevo_intento


# -----------------------------------------------------------------------------
# 2. GUARDADO PARCIAL (HEARTBEAT)
# -----------------------------------------------------------------------------
@router.patch("/{simulacro_id}/guardar", response_model=RespuestaEstudianteResponse)
def guardar_progreso(
    simulacro_id: int,
    data: RespuestaEstudianteUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    intento = db.query(RespuestaEstudiante).filter(
        RespuestaEstudiante.simulacro_id == simulacro_id,
        RespuestaEstudiante.usuario_id == current_user.id,
        RespuestaEstudiante.anulado.is_(False)
    ).first()

    if not intento:
        raise HTTPException(status_code=404, detail="No tienes un intento activo para este simulacro")

    if intento.fecha_finalizacion:
        raise HTTPException(status_code=400, detail="El intento ya fue finalizado")

    db_simulacro = db.query(Simulacro).filter(Simulacro.id == simulacro_id).first()
    fecha_inicio = _ensure_aware(intento.fecha_inicio)
    limite = _calcular_limite(fecha_inicio, db_simulacro.duracion_minutos)
    if limite and _now_utc() > limite:
        raise HTTPException(status_code=400, detail="El tiempo para este simulacro ha expirado.")

    respuestas_actuales = dict(intento.respuestas) if intento.respuestas else {}
    respuestas_actuales.update(data.respuestas_parciales or {})
    intento.respuestas = respuestas_actuales

    if data.tiempo_empleado is not None:
        intento.tiempo_empleado = max(0, int(data.tiempo_empleado))

    db.commit()
    db.refresh(intento)
    return intento


# -----------------------------------------------------------------------------
# 3. FINALIZAR SIMULACRO (VALIDACIÓN SERVER-SIDE)
# -----------------------------------------------------------------------------
@router.post("/{simulacro_id}/finalizar", response_model=RespuestaEstudianteResponse)
async def finalizar_simulacro(
    simulacro_id: int,
    entrega: RespuestaEstudianteFinalize,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    submission_lock = None
    try:
        from app.core.redis_config import is_redis_available, get_redis
        if is_redis_available():
            lock_key = f"lock:simulacro_submit:{simulacro_id}:{current_user.id}"
            redis_client = get_redis()
            acquired = redis_client.set(lock_key, "1", nx=True, ex=30)
            if not acquired:
                raise HTTPException(
                    status_code=409,
                    detail="Tu respuesta está siendo procesada. Por favor espera unos segundos."
                )
            submission_lock = lock_key
    except HTTPException:
        raise
    except Exception as e:
        print(f"Warning: Redis lock failed: {e}")

    try:
        db_simulacro = db.query(Simulacro).filter(Simulacro.id == simulacro_id).first()
        if not db_simulacro:
            raise HTTPException(status_code=404, detail="Simulacro no encontrado")

        intento = db.query(RespuestaEstudiante).filter(
            RespuestaEstudiante.simulacro_id == simulacro_id,
            RespuestaEstudiante.usuario_id == current_user.id,
            RespuestaEstudiante.anulado.is_(False)
        ).first()

        if not intento:
            raise HTTPException(status_code=404, detail="No existe intento activo para finalizar. Debes iniciar primero.")

        if intento.fecha_finalizacion:
            raise HTTPException(status_code=400, detail="Este simulacro ya fue finalizado previamente.")

        if not intento.fecha_inicio:
            intento.fecha_inicio = _now_utc()
            db.commit()
            db.refresh(intento)

        fecha_inicio = _ensure_aware(intento.fecha_inicio)
        limite = _calcular_limite(fecha_inicio, db_simulacro.duracion_minutos)
        minimo = _calcular_minimo(fecha_inicio, db_simulacro.duracion_minutos)
        now = _now_utc()

        if minimo and now < minimo:
            remaining = int((minimo - now).total_seconds())
            raise HTTPException(
                status_code=400,
                detail=f"Debes permanecer al menos el 30% del tiempo antes de finalizar. Faltan {max(0, remaining)} segundos."
            )

        if limite and now > limite:
            respuestas_finales = dict(intento.respuestas) if intento.respuestas else {}
            contenido = db_simulacro.contenido
            if isinstance(contenido, str):
                import json
                contenido = json.loads(contenido)

            respuestas_detalladas, total_correctas, total_incorrectas, puntaje = _calcular_resultados(
                contenido, respuestas_finales
            )

            intento.respuestas = respuestas_finales
            intento.respuestas_detalladas = respuestas_detalladas
            intento.total_correctas = total_correctas
            intento.total_incorrectas = total_incorrectas
            intento.puntaje_total = puntaje
            intento.tiempo_empleado = int(min((limite - fecha_inicio).total_seconds(), db_simulacro.duracion_minutos * 60))
            intento.fecha_finalizacion = limite

            db.commit()
            db.refresh(intento)

            if not intento.fraude:
                background_tasks.add_task(AnalisisService.procesar_respuesta, intento.id)

            raise HTTPException(status_code=400, detail="El tiempo para este simulacro ha expirado. Se guardaron las respuestas parciales.")

        contenido = db_simulacro.contenido
        if isinstance(contenido, str):
            import json
            contenido = json.loads(contenido)

        respuestas_finales = dict(intento.respuestas) if intento.respuestas else {}
        respuestas_finales.update(entrega.respuestas or {})

        respuestas_detalladas, total_correctas, total_incorrectas, puntaje = _calcular_resultados(
            contenido, respuestas_finales
        )

        if limite:
            tiempo_empleado = int(min((now - fecha_inicio).total_seconds(), db_simulacro.duracion_minutos * 60))
        else:
            tiempo_empleado = max(0, int(entrega.tiempo_empleado or 0))

        intento.respuestas = respuestas_finales
        intento.respuestas_detalladas = respuestas_detalladas
        intento.total_correctas = total_correctas
        intento.total_incorrectas = total_incorrectas
        intento.puntaje_total = puntaje
        intento.tiempo_empleado = tiempo_empleado
        intento.fecha_finalizacion = now

        db.commit()
        db.refresh(intento)

        if not intento.fraude:
            background_tasks.add_task(AnalisisService.procesar_respuesta, intento.id)

        try:
            from app.core.websocket_manager import manager
            payload = {
                "evento": "simulacro_finalizado",
                "data": {
                    "estudiante_id": intento.usuario_id,
                    "estudiante_nombre": current_user.nombre or current_user.email,
                    "simulacro_id": simulacro_id,
                    "respuesta_id": intento.id,
                    "puntaje": float(intento.puntaje_total) if intento.puntaje_total is not None else 0.0,
                    "fraude": intento.fraude
                },
                "server_time": now.isoformat()
            }
            await manager.broadcast_to_institution(payload, intento.institucion_id)
        except Exception as e:
            print(f"❌ Error notificando finalización WS: {e}")

        return intento

    finally:
        if submission_lock:
            try:
                redis_client = get_redis()
                redis_client.delete(submission_lock)
            except Exception:
                pass

@router.get("/{simulacro_id}/mi-intento", response_model=RespuestaEstudianteResponse)
def read_mi_intento(
    simulacro_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    intento = db.query(RespuestaEstudiante).filter(
        RespuestaEstudiante.simulacro_id == simulacro_id,
        RespuestaEstudiante.usuario_id == current_user.id
    ).first()
    
    if not intento:
        raise HTTPException(status_code=404, detail="No se encontró un intento para este simulacro")
        
    return intento

@router.get("/{simulacro_id}/intentos/{usuario_id}", response_model=RespuestaEstudianteResponse)
def read_intento_estudiante(
    simulacro_id: int,
    usuario_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Permite a un admin/docente ver el intento de un estudiante específico.
    """
    # 1. Validar Rol
    if current_user.rol.nombre == 'estudiante':
        raise HTTPException(status_code=403, detail="No tiene permisos para ver intentos de otros usuarios")

    # 2. Buscar Intento
    intento = db.query(RespuestaEstudiante).filter(
        RespuestaEstudiante.simulacro_id == simulacro_id,
        RespuestaEstudiante.usuario_id == usuario_id,
        RespuestaEstudiante.anulado.is_(False)
    ).first()
    
    if not intento:
        raise HTTPException(status_code=404, detail="El estudiante no ha realizado este simulacro o no existe")

    # 3. Validar Institución (si aplica)
    # El usuario del intento debe pertenecer a la misma institución que el admin
    if current_user.rol.nombre == 'admin':
        # Cargar usuario del intento para verificar inst
        estudiante = db.query(Usuario).get(usuario_id)
        if not estudiante or estudiante.institucion_id != current_user.institucion_id:
             raise HTTPException(status_code=403, detail="No tiene permisos para ver datos de este estudiante")

    return intento
