import io
from fastapi import Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user
from app.database.config import get_db
from app.models.reporte_grupal import ReporteGrupal
from app.models.usuario import Usuario
from app.services.analisis_service import AnalisisService
from app.services.pdf_report_service import PDFReportService

from app.api.simulacros_router import router


def _validar_admin(current_user: Usuario) -> int:
    if not current_user.rol or current_user.rol.nombre != "admin":
        raise HTTPException(status_code=403, detail="Solo admin puede gestionar reportes grupales")

    inst_id = current_user.institucion_id
    if not inst_id:
        raise HTTPException(status_code=400, detail="Usuario sin institución asignada")

    return inst_id


def _is_group_numeric_complete(data) -> bool:
    if not isinstance(data, dict):
        return False
    if data.get("tipo_reporte") != "grupal_numerico":
        return False
    if "average_score_100" not in data:
        return False
    if not data.get("performance_level"):
        return False
    students = data.get("students")
    if not isinstance(students, list) or len(students) == 0:
        return False
    return True

@router.get("/{simulacro_id}/reporte-grupal")
def get_reporte_grupal(
    simulacro_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Obtiene el reporte grupal del simulacro para la institución del usuario actual.
    """
    inst_id = _validar_admin(current_user)

    reporte = db.query(ReporteGrupal).filter(
        ReporteGrupal.simulacro_id == simulacro_id,
        ReporteGrupal.institucion_id == inst_id
    ).first()
    
    if not reporte or reporte.anulado:
        return {"exists": False}

    data = reporte.estadisticas_agregadas if isinstance(reporte.estadisticas_agregadas, dict) else None
    es_numerico = bool(data and data.get("tipo_reporte") == "grupal_numerico")

    # Auto-refresh solo para reportes numéricos incompletos de versiones previas.
    # No toca reportes IA legacy.
    if es_numerico and not _is_group_numeric_complete(data):
        informe_txt, metadata = AnalisisService.generar_reporte_grupal(simulacro_id, inst_id)
        if informe_txt:
            reporte.informe_contenido = informe_txt
            reporte.estadisticas_agregadas = metadata
            db.add(reporte)
            db.commit()
            db.refresh(reporte)
            data = reporte.estadisticas_agregadas
            es_numerico = True

    payload = {
        "exists": True,
        "informe": reporte.informe_contenido,
        "estadisticas": reporte.estadisticas_agregadas,
        "tipo_contenido": "numerico" if es_numerico else "markdown",
        "created_at": reporte.created_at
    }
    if es_numerico:
        payload["data"] = data or reporte.estadisticas_agregadas
    return payload

@router.post("/{simulacro_id}/reporte-grupal")
def generate_reporte_grupal(
    simulacro_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Genera reporte grupal numérico determinístico.
    """
    inst_id = _validar_admin(current_user)

    # 1. Check existing
    existing = db.query(ReporteGrupal).filter(
        ReporteGrupal.simulacro_id == simulacro_id,
        ReporteGrupal.institucion_id == inst_id
    ).first()
    
    if existing and not existing.anulado:
        existing_data = existing.estadisticas_agregadas if isinstance(existing.estadisticas_agregadas, dict) else None
        es_numerico = bool(existing_data and existing_data.get("tipo_reporte") == "grupal_numerico")

        # Si es numérico pero incompleto (p.ej. sin performance_level), lo regeneramos.
        if es_numerico and not _is_group_numeric_complete(existing_data):
            informe_txt, metadata = AnalisisService.generar_reporte_grupal(simulacro_id, inst_id)
            if not informe_txt:
                raise HTTPException(status_code=400, detail=metadata.get("error", "Error generando reporte grupal"))

            existing.informe_contenido = informe_txt
            existing.estadisticas_agregadas = metadata
            existing.anulado = False
            db.add(existing)
            db.commit()
            db.refresh(existing)

            return {
                "exists": True,
                "informe": existing.informe_contenido,
                "estadisticas": existing.estadisticas_agregadas,
                "tipo_contenido": "numerico",
                "data": existing.estadisticas_agregadas,
                "created_at": existing.created_at
            }

        payload = {
            "exists": True,
            "informe": existing.informe_contenido,
            "estadisticas": existing.estadisticas_agregadas,
            "tipo_contenido": "numerico" if es_numerico else "markdown",
            "created_at": existing.created_at
        }
        if es_numerico:
            payload["data"] = existing.estadisticas_agregadas
        return payload

    # 2. Generar
    informe_txt, metadata = AnalisisService.generar_reporte_grupal(simulacro_id, inst_id)
    
    if not informe_txt:
        raise HTTPException(status_code=400, detail=metadata.get("error", "Error generando reporte grupal"))

    # 3. Guardar
    if existing:
        existing.informe_contenido = informe_txt
        existing.estadisticas_agregadas = metadata
        existing.anulado = False
        db.add(existing)
        db.commit()
        db.refresh(existing)
        nuevo = existing
    else:
        nuevo = ReporteGrupal(
            simulacro_id=simulacro_id,
            institucion_id=inst_id,
            informe_contenido=informe_txt,
            estadisticas_agregadas=metadata
        )
        db.add(nuevo)
        db.commit()
        db.refresh(nuevo)
    
    return {
        "exists": True,
        "informe": nuevo.informe_contenido,
        "estadisticas": nuevo.estadisticas_agregadas,
        "tipo_contenido": "numerico",
        "data": nuevo.estadisticas_agregadas,
        "created_at": nuevo.created_at
    }


@router.get("/{simulacro_id}/reporte-grupal/pdf")
def get_reporte_grupal_pdf(
    simulacro_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Descarga PDF del reporte grupal numérico.
    """
    inst_id = _validar_admin(current_user)

    reporte = db.query(ReporteGrupal).filter(
        ReporteGrupal.simulacro_id == simulacro_id,
        ReporteGrupal.institucion_id == inst_id,
        ReporteGrupal.anulado.is_(False)
    ).first()

    data = None
    if reporte and isinstance(reporte.estadisticas_agregadas, dict):
        if reporte.estadisticas_agregadas.get("tipo_reporte") == "grupal_numerico":
            data = reporte.estadisticas_agregadas

    # Si no hay versión numérica persistida (p.ej. reporte IA legacy), calcular al vuelo.
    if (
        (not data)
        or (not isinstance(data.get("students"), list))
        or (len(data.get("students", [])) == 0)
        or (not data.get("performance_level"))
    ):
        informe_txt, metadata = AnalisisService.generar_reporte_grupal(simulacro_id, inst_id)
        if not informe_txt:
            raise HTTPException(status_code=400, detail=metadata.get("error", "No fue posible generar el reporte grupal"))
        data = metadata

    buffer = io.BytesIO()
    PDFReportService.generate_group_area_report(buffer, data)
    buffer.seek(0)

    area = (data.get("area_display") or data.get("area") or "Area").replace(" ", "_")
    institucion = (data.get("institution_name") or "SinInstitucion").replace(" ", "_")
    filename = f"Reporte_Grupal_{institucion}_{area}.pdf"

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
