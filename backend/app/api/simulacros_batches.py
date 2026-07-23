import re
from typing import Optional

from fastapi import Depends, HTTPException, Query
from sqlalchemy import func, distinct
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user
from app.database.config import get_db
from app.models.simulacro import Simulacro
from app.models.usuario import Usuario
from app.services.analisis_service import AnalisisService

from app.api.simulacros_router import router

AREAS_ICFES = {
    "MATEMATICAS", "LECTURA_CRITICA", "CIENCIAS_NATURALES",
    "SOCIALES_CIUDADANAS", "INGLES"
}


def _sanitize_batch(s: str) -> str:
    return re.sub(r'[^a-z0-9]+', '-', s.lower().strip())[:60]


def _validar_admin_inst(current_user: Usuario) -> int:
    if not current_user.rol or current_user.rol.nombre != "admin":
        raise HTTPException(status_code=403, detail="Solo admin puede acceder a batches")
    inst_id = current_user.institucion_id
    if not inst_id:
        raise HTTPException(status_code=400, detail="Usuario sin institución asignada")
    return inst_id


def _batch_info(db: Session, batch_id: str, institucion_id: int) -> dict:
    simulacros = db.query(Simulacro).filter(
        Simulacro.batch_id == batch_id,
        Simulacro.institucion_id == institucion_id
    ).order_by(Simulacro.area, Simulacro.sede_id).all()

    if not simulacros:
        return None

    areas_unicas = list(dict.fromkeys(s.area for s in simulacros))
    areas_faltantes = sorted(AREAS_ICFES - set(areas_unicas))
    primero = simulacros[0]

    titulo_base = primero.titulo if primero else ""
    match = re.match(r'^(.*?)\s*-\s*(Matemáticas|Lectura Crítica|Ciencias Naturales|Sociales y Ciudadanas|Inglés)', titulo_base)
    if match:
        titulo_base = match.group(1).strip()

    # Obtener sedes únicas asociadas al batch
    sede_ids = list(dict.fromkeys(s.sede_id for s in simulacros if s.sede_id is not None))
    duracion_minutos = primero.duracion_minutos if primero else 60

    return {
        "batch_id": batch_id,
        "titulo_base": titulo_base,
        "fecha_creacion": primero.created_at.isoformat() if primero.created_at else None,
        "institucion_id": institucion_id,
        "num_preguntas": primero.total_preguntas,
        "duracion_minutos": duracion_minutos,
        "sede_ids": sede_ids,
        "areas_cubiertas": areas_unicas,
        "areas_faltantes": areas_faltantes,
        "completo": len(areas_unicas) >= len(AREAS_ICFES),
        "total_simulacros": len(simulacros),
        "simulacros": [
            {
                "id": s.id,
                "titulo": s.titulo,
                "area": s.area,
                "sede_id": s.sede_id,
                "estado": s.estado,
                "activo": s.activo,
                "total_preguntas": s.total_preguntas,
            }
            for s in simulacros
        ]
    }


@router.get("/batches")
def list_batches(
    institucion_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user),
):
    if not current_user.rol or current_user.rol.nombre != "admin":
        raise HTTPException(status_code=403, detail="Solo admin puede acceder a batches")

    if current_user.institucion_id is not None:
        inst_id = current_user.institucion_id
        batches_ids = db.query(distinct(Simulacro.batch_id)).filter(
            Simulacro.batch_id.isnot(None),
            Simulacro.institucion_id == inst_id
        ).order_by(Simulacro.batch_id.desc()).all()

        result = []
        for (bid,) in batches_ids:
            info = _batch_info(db, bid, inst_id)
            if info:
                result.append(info)
        return result
    else:
        # Super Admin
        if institucion_id:
            inst_id = institucion_id
            batches_ids = db.query(distinct(Simulacro.batch_id)).filter(
                Simulacro.batch_id.isnot(None),
                Simulacro.institucion_id == inst_id
            ).order_by(Simulacro.batch_id.desc()).all()

            result = []
            for (bid,) in batches_ids:
                info = _batch_info(db, bid, inst_id)
                if info:
                    result.append(info)
            return result
        else:
            # Obtener todos los batches de todas las instituciones
            batches_query = db.query(Simulacro.batch_id, Simulacro.institucion_id).filter(
                Simulacro.batch_id.isnot(None)
            ).distinct(Simulacro.batch_id).all()

            result = []
            seen_batches = set()
            for bid, bid_inst_id in batches_query:
                if bid in seen_batches:
                    continue
                seen_batches.add(bid)
                info = _batch_info(db, bid, bid_inst_id)
                if info:
                    result.append(info)
            # Ordenar por fecha_creacion desc si existe, de lo contrario por batch_id desc
            result.sort(key=lambda x: x.get("fecha_creacion") or "", reverse=True)
            return result


@router.get("/batches/{batch_id}")
def get_batch(
    batch_id: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user),
):
    if not current_user.rol or current_user.rol.nombre != "admin":
        raise HTTPException(status_code=403, detail="Solo admin puede acceder a batches")

    if current_user.institucion_id is not None:
        inst_id = current_user.institucion_id
    else:
        # Super Admin: Deducir institución del batch
        sim = db.query(Simulacro).filter(Simulacro.batch_id == batch_id).first()
        if not sim:
            raise HTTPException(status_code=404, detail="Batch no encontrado")
        inst_id = sim.institucion_id

    info = _batch_info(db, batch_id, inst_id)
    if info is None:
        raise HTTPException(status_code=404, detail="Batch no encontrado")
    return info


@router.get("/batch-suggestions")
def batch_suggestions(
    nombre_base: str = Query(..., min_length=1),
    institucion_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user),
):
    if not current_user.rol or current_user.rol.nombre != "admin":
        raise HTTPException(status_code=403, detail="Solo admin puede acceder a batches")

    if current_user.institucion_id is not None:
        inst_id = current_user.institucion_id
    else:
        if institucion_id:
            inst_id = institucion_id
        else:
            raise HTTPException(status_code=400, detail="Debe especificar institucion_id para sugerencias como Super Admin")

    prefix = _sanitize_batch(nombre_base)

    batches_ids = db.query(distinct(Simulacro.batch_id)).filter(
        Simulacro.batch_id.isnot(None),
        Simulacro.batch_id.like(f"{prefix}%"),
        Simulacro.institucion_id == inst_id
    ).order_by(Simulacro.batch_id.desc()).all()

    suggestions = []
    for (bid,) in batches_ids:
        info = _batch_info(db, bid, inst_id)
        if info and not info["completo"]:
            suggestions.append({
                "batch_id": info["batch_id"],
                "titulo_base": info["titulo_base"],
                "fecha_creacion": info["fecha_creacion"],
                "num_preguntas": info["num_preguntas"],
                "duracion_minutos": info["duracion_minutos"],
                "sede_ids": info["sede_ids"],
                "areas_cubiertas": info["areas_cubiertas"],
                "areas_faltantes": info["areas_faltantes"],
            })

    return suggestions



