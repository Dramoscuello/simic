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

    return {
        "batch_id": batch_id,
        "titulo_base": titulo_base,
        "fecha_creacion": primero.created_at.isoformat() if primero.created_at else None,
        "institucion_id": institucion_id,
        "num_preguntas": primero.total_preguntas,
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
    inst_id = _validar_admin_inst(current_user)
    if current_user.institucion_id is None:
        if institucion_id:
            inst_id = institucion_id
        else:
            return []

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


@router.get("/batches/{batch_id}")
def get_batch(
    batch_id: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user),
):
    inst_id = _validar_admin_inst(current_user)
    info = _batch_info(db, batch_id, inst_id)
    if info is None:
        raise HTTPException(status_code=404, detail="Batch no encontrado")
    return info


@router.get("/batch-suggestions")
def batch_suggestions(
    nombre_base: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user),
):
    inst_id = _validar_admin_inst(current_user)
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
                "areas_cubiertas": info["areas_cubiertas"],
                "areas_faltantes": info["areas_faltantes"],
            })

    return suggestions


@router.post("/batches/{batch_id}/reporte-global")
def generate_global_report(
    batch_id: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user),
):
    inst_id = _validar_admin_inst(current_user)

    batch = _batch_info(db, batch_id, inst_id)
    if batch is None:
        raise HTTPException(status_code=404, detail="Batch no encontrado")

    if batch["completo"]:
        areas_a_reportar = list(AREAS_ICFES)
    else:
        areas_a_reportar = batch["areas_cubiertas"]

    reporte = AnalisisService.generar_reporte_global(batch_id, inst_id, areas_a_reportar)
    if reporte is None:
        raise HTTPException(status_code=400, detail="No se pudo generar el reporte global")

    return reporte


@router.get("/batches/{batch_id}/reporte-global/pdf")
def download_global_report_pdf(
    batch_id: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user),
):
    import io
    from fastapi.responses import StreamingResponse
    from app.services.pdf_report_service import PDFReportService

    inst_id = _validar_admin_inst(current_user)

    batch = _batch_info(db, batch_id, inst_id)
    if batch is None:
        raise HTTPException(status_code=404, detail="Batch no encontrado")

    areas = list(AREAS_ICFES) if batch["completo"] else batch["areas_cubiertas"]
    reporte = AnalisisService.generar_reporte_global(batch_id, inst_id, areas)
    if reporte is None or "error" in reporte:
        raise HTTPException(status_code=400, detail="No se pudo generar el reporte global")

    buffer = io.BytesIO()
    PDFReportService.generate_global_batch_report(buffer, reporte)
    buffer.seek(0)

    filename = f"Diagnostico_Global_{batch_id}.pdf"
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
