import os
import json
from datetime import datetime, timedelta, timezone

from app.database.config import session_Local
from app.models.respuesta_estudiante import RespuestaEstudiante
from app.models.simulacro import Simulacro


MARGEN_TOLERANCIA_MIN = int(os.getenv("SIMULACRO_MARGIN_MINUTES", "5"))
BATCH_SIZE = int(os.getenv("SIMULACRO_REAPER_BATCH", "200"))


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _ensure_aware(dt: datetime) -> datetime:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


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

def close_expired_attempts():
    db = session_Local()
    now = _now_utc()
    try:
        intentos = (
            db.query(RespuestaEstudiante)
            .join(Simulacro, RespuestaEstudiante.simulacro_id == Simulacro.id)
            .filter(RespuestaEstudiante.fecha_finalizacion == None)  # noqa: E711
            .filter(RespuestaEstudiante.fecha_inicio != None)  # noqa: E711
            .filter(RespuestaEstudiante.anulado.is_(False))
            .filter(Simulacro.duracion_minutos != None)  # noqa: E711
            .limit(BATCH_SIZE)
            .all()
        )

        for intento in intentos:
            try:
                simulacro = intento.simulacro
                fecha_inicio = _ensure_aware(intento.fecha_inicio)
                if not fecha_inicio or not simulacro.duracion_minutos:
                    continue

                limite = fecha_inicio + timedelta(
                    minutes=simulacro.duracion_minutos + MARGEN_TOLERANCIA_MIN
                )

                if now <= limite:
                    continue

                contenido = simulacro.contenido
                if isinstance(contenido, str):
                    contenido = json.loads(contenido)

                respuestas_finales = dict(intento.respuestas) if intento.respuestas else {}
                respuestas_detalladas, total_correctas, total_incorrectas, puntaje = _calcular_resultados(
                    contenido, respuestas_finales
                )

                intento.respuestas = respuestas_finales
                intento.respuestas_detalladas = respuestas_detalladas
                intento.total_correctas = total_correctas
                intento.total_incorrectas = total_incorrectas
                intento.puntaje_total = puntaje
                intento.tiempo_empleado = int(
                    min((limite - fecha_inicio).total_seconds(), simulacro.duracion_minutos * 60)
                )
                intento.fecha_finalizacion = limite

                db.commit()

                # Nota: No generar informe IA cuando el cierre es automático (reaper).
                # Esto evita reportes con muy pocas respuestas.

            except Exception as e:
                db.rollback()
                print(f"[reaper] Error cerrando intento {getattr(intento, 'id', 'unknown')}: {e}")

    finally:
        db.close()


if __name__ == "__main__":
    close_expired_attempts()
