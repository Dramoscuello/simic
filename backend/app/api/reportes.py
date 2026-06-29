import io

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.database.config import get_db
from app.api.deps import get_current_active_user
from app.models.usuario import Usuario
from app.models.respuesta_estudiante import RespuestaEstudiante
from app.models.reporte_grupal import ReporteGrupal
from app.models.simulacro import Simulacro
from app.services.analisis_service import AnalisisService
from app.services.pdf_report_service import PDFReportService
from pydantic import BaseModel

router = APIRouter(
    prefix="/reportes",
    tags=["reportes"]
)

AREA_DISPLAY_MAP = {
    "MATEMATICAS": "Matemáticas",
    "LECTURA_CRITICA": "Lectura Crítica",
    "SOCIALES_CIUDADANAS": "Sociales y Ciudadanas",
    "CIENCIAS_NATURALES": "Ciencias Naturales",
    "INGLES": "Inglés",
}


def _safe_filename_part(raw: str, default: str) -> str:
    base = raw or default
    cleaned = "".join(ch for ch in base if ch.isalnum() or ch in ("_", "-"))
    return cleaned or default

# --- SCHEMAS ---
class DashboardStats(BaseModel):
    total_estudiantes_activos: int
    promedio_global: float
    areas_criticas: List[str]
    total_simulacros_realizados: int

class ReporteItem(BaseModel):
    id: int # ID del reporte o respuesta
    titulo: str
    subtitulo: str
    fecha: datetime
    puntaje: Optional[float] = None
    tags: List[str] = []
    metadata: Dict[str, Any] = {} # IDs relacionados (usuario_id, simulacro_id, etc)
    tipo_reporte: str # "individual", "grupal"
    fraude: bool = False # Nuevo campo

class DashboardData(BaseModel):
    stats: DashboardStats
    individuales: List[ReporteItem]
    grupales: List[ReporteItem]

# --- ENDPOINTS ---

@router.get("/dashboard", response_model=DashboardData)
def get_dashboard_data(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Retorna toda la data necesaria para el Dashboard de Reportes (Admin Institucional).
    Estructura de 3 columnas + Stats.
    """
    # Validar permisos
    if current_user.rol.nombre not in ['admin', 'docente']:
        # Los estudiantes no ven este dashboard, ven el suyo propio
        raise HTTPException(status_code=403, detail="No tiene permisos para ver el dashboard institucional.")
    
    inst_id = current_user.institucion_id
    sede_id = current_user.sede_id if current_user.rol.nombre == 'docente' else None
    
    # Helper to add sede filter to query on RespuestaEstudiante
    from app.models.usuario import Usuario as UserModel
    def _scope_r(query):
        if sede_id:
            return query.join(UserModel, UserModel.id == RespuestaEstudiante.usuario_id)\
                        .filter(UserModel.sede_id == sede_id)
        return query

    # Filtro base para todas las queries
    if current_user.rol.nombre == 'admin' and not inst_id:
        pass

    # 1. STATS (Cálculo rápido)
    # Total estudiantes que han presentado al menos un examen
    q_est = db.query(RespuestaEstudiante.usuario_id).distinct().filter(RespuestaEstudiante.anulado.is_(False))
    if inst_id:
        q_est = q_est.filter(RespuestaEstudiante.institucion_id == inst_id)
    q_est = _scope_r(q_est) if sede_id else q_est
    total_estudiantes = q_est.count()
    
    # Total simulacros realizados
    q_sims = db.query(RespuestaEstudiante).filter(RespuestaEstudiante.anulado.is_(False))
    if inst_id:
        q_sims = q_sims.filter(RespuestaEstudiante.institucion_id == inst_id)
    q_sims = _scope_r(q_sims) if sede_id else q_sims
    total_simulacros = q_sims.count()
    
    # Promedio global
    from sqlalchemy import func
    avg_score = db.query(func.avg(RespuestaEstudiante.puntaje_total)).filter(RespuestaEstudiante.anulado.is_(False))
    if inst_id:
        avg_score = avg_score.filter(RespuestaEstudiante.institucion_id == inst_id)
    avg_score = _scope_r(avg_score) if sede_id else avg_score
    promedio = avg_score.scalar() or 0.0

    # Identificar Áreas Críticas (Bottom 2 por promedio)
    from sqlalchemy import func
    criticas_query = db.query(
        Simulacro.area,
        func.avg(RespuestaEstudiante.puntaje_total).label('promedio')
    ).join(RespuestaEstudiante)\
     .filter(RespuestaEstudiante.puntaje_total != None)\
     .filter(RespuestaEstudiante.anulado.is_(False))
    
    if inst_id:
        criticas_query = criticas_query.filter(RespuestaEstudiante.institucion_id == inst_id)
    criticas_query = _scope_r(criticas_query) if sede_id else criticas_query
        
    criticas_result = criticas_query.group_by(Simulacro.area)\
        .order_by(func.avg(RespuestaEstudiante.puntaje_total).asc())\
        .limit(2)\
        .all()
        
    areas_criticas = [r.area for r in criticas_result]

    stats = DashboardStats(
        total_estudiantes_activos=total_estudiantes,
        promedio_global=round(float(promedio), 1),
        areas_criticas=areas_criticas if areas_criticas else ["Sin datos suficientes"],
        total_simulacros_realizados=total_simulacros
    )

    # 2. REPORTES INDIVIDUALES (Últimos 5 con análisis IA generado)
    # Tabla: respuestas_estudiantes (campo analisis_ia != null)
    q_ind = db.query(RespuestaEstudiante).filter(
        RespuestaEstudiante.analisis_ia != None,
        RespuestaEstudiante.anulado.is_(False)
    )
    if inst_id:
        q_ind = q_ind.filter(RespuestaEstudiante.institucion_id == inst_id)
    q_ind = _scope_r(q_ind) if sede_id else q_ind
    
    individuales_db = q_ind.order_by(RespuestaEstudiante.updated_at.desc()).limit(5).all()
    
    individuales = []
    for r in individuales_db:
        titulo = r.simulacro.area if r.simulacro else "Simulacro"
        tags = [titulo[:3].upper()]

        individuales.append(ReporteItem(
            id=r.id, # ID de la respuesta
            titulo=titulo,
            subtitulo=r.usuario.nombre if r.usuario else "Estudiante",
            fecha=r.updated_at or r.created_at,
            puntaje=float(r.puntaje_total) if r.puntaje_total is not None else 0,
            tags=tags,
            metadata={
                "usuario_id": r.usuario_id,
                "simulacro_id": r.simulacro_id,
                "informe_url": f"/simulacros/{r.simulacro_id}/reporte/{r.usuario_id}" # Endpoint ficticio para abrir modal
            },
            tipo_reporte="individual",
            fraude=r.fraude # Mapear fraude
        ))

    # 3. REPORTES GRUPALES (ReporteGrupal)
    q_grup = db.query(ReporteGrupal).options(joinedload(ReporteGrupal.simulacro)).filter(ReporteGrupal.anulado.is_(False))
    if inst_id:
        q_grup = q_grup.filter(ReporteGrupal.institucion_id == inst_id)
    
    grupales_db = q_grup.order_by(ReporteGrupal.created_at.desc()).limit(5).all()
    
    grupales = []
    for g in grupales_db:
        sim_titulo = g.simulacro.titulo if g.simulacro else "Simulacro General"
        area = g.simulacro.area if g.simulacro else "General"
        
        grupales.append(ReporteItem(
            id=g.id,
            titulo=f"Diagnóstico: {area}",
            subtitulo=sim_titulo,
            fecha=g.created_at,
            tags=["GRUPAL", area[:3].upper()],
            metadata={
                "simulacro_id": g.simulacro_id,
                "institucion_id": g.institucion_id
            },
            tipo_reporte="grupal"
        ))

    return DashboardData(
        stats=stats,
        individuales=individuales,
        grupales=grupales
    )


class ReporteDetalle(BaseModel):
    titulo: str
    subtitulo: Optional[str] = None
    contenido: Optional[str] = None # Markdown o HTML (Legacy)
    data: Optional[Dict[str, Any]] = None # Nuevo campo estructurado
    tipo_contenido: str = "markdown" # "markdown", "numerico"
    fraude: bool = False

@router.get("/detalle/{tipo_reporte}/{id}", response_model=ReporteDetalle)
def get_reporte_detalle(
    tipo_reporte: str,
    id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """Retorna el contenido completo de un reporte específico."""
    inst_id = current_user.institucion_id
    if current_user.rol.nombre not in ['admin', 'docente']:
        raise HTTPException(status_code=403, detail="No tiene permisos.")
    
    # 1. INDIVIDUAL
    if tipo_reporte == "individual":
        resp = db.query(RespuestaEstudiante).filter(RespuestaEstudiante.id == id).first()
        if not resp: raise HTTPException(404, "Reporte no encontrado")
        if resp.anulado:
            raise HTTPException(404, "Reporte no encontrado")
        
        # Validación de seguridad
        if current_user.rol.nombre != 'admin' and resp.institucion_id != inst_id:
             raise HTTPException(403, "No autorizado (Pertenece a otra institución)")
        
        analisis = resp.analisis_ia or {}
        informe = analisis.get("informe_ia") or "Contenido no disponible o aún no generado."
        
        return ReporteDetalle(
            titulo=f"Reporte Individual: {resp.usuario.nombre}",
            subtitulo=f"{resp.simulacro.titulo} - {resp.simulacro.area}",
            contenido=informe,
            fraude=resp.fraude # Mapear valor
        )

    # 2. GRUPAL
    elif tipo_reporte == "grupal":
        grup = db.query(ReporteGrupal).filter(ReporteGrupal.id == id).first()
        if not grup: raise HTTPException(404, "Reporte no encontrado")
        if grup.anulado:
            raise HTTPException(404, "Reporte no encontrado")
        
        if current_user.rol.nombre != 'admin' and grup.institucion_id != inst_id:
             raise HTTPException(403, "No autorizado")

        # Nuevo formato: reporte grupal numérico determinístico
        if isinstance(grup.estadisticas_agregadas, dict):
            data = grup.estadisticas_agregadas
            if data.get("tipo_reporte") == "grupal_numerico" and "average_score_100" in data:
                return ReporteDetalle(
                    titulo=f"Diagnóstico Grupal: {grup.simulacro.titulo if grup.simulacro else 'Simulacro'}",
                    subtitulo=f"Área: {grup.simulacro.area if grup.simulacro else 'General'}",
                    data=data,
                    tipo_contenido="numerico"
                )
        
        return ReporteDetalle(
            titulo=f"Diagnóstico Grupal: {grup.simulacro.titulo if grup.simulacro else 'Simulacro'}",
            subtitulo=f"Área: {grup.simulacro.area if grup.simulacro else 'General'}",
            contenido=grup.informe_contenido
        )
    
    else:
        raise HTTPException(400, "Tipo de reporte inválido (individual, grupal)")


@router.get("/detalle/{tipo_reporte}/{id}/pdf")
def get_reporte_detalle_pdf(
    tipo_reporte: str,
    id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Descarga PDF de alta calidad desde backend.
    Actualmente soporta reporte individual IA.
    """
    inst_id = current_user.institucion_id
    if current_user.rol.nombre not in ["admin", "docente"]:
        raise HTTPException(status_code=403, detail="No tiene permisos.")

    if tipo_reporte != "individual":
        raise HTTPException(status_code=400, detail="Solo se soporta PDF backend para reporte individual desde este endpoint.")

    resp = db.query(RespuestaEstudiante).options(
        joinedload(RespuestaEstudiante.usuario).joinedload(Usuario.grupo),
        joinedload(RespuestaEstudiante.institucion),
        joinedload(RespuestaEstudiante.simulacro),
    ).filter(RespuestaEstudiante.id == id).first()

    if not resp or resp.anulado:
        raise HTTPException(status_code=404, detail="Reporte no encontrado")

    if current_user.rol.nombre != "admin" and resp.institucion_id != inst_id:
        raise HTTPException(status_code=403, detail="No autorizado (Pertenece a otra institución)")

    if resp.fraude:
        raise HTTPException(status_code=400, detail="El informe IA no está disponible para intentos con fraude.")

    analisis = resp.analisis_ia or {}
    informe = analisis.get("informe_ia")
    if not informe or not str(informe).strip():
        raise HTTPException(status_code=400, detail="El informe IA aún no está disponible.")

    area_raw = resp.simulacro.area if resp.simulacro else "N/A"
    area_display = AREA_DISPLAY_MAP.get(area_raw, area_raw.replace("_", " ").title())
    score = float(resp.puntaje_total) if resp.puntaje_total is not None else 0.0
    generated_at = (resp.updated_at or resp.created_at or datetime.now()).strftime("%Y-%m-%d %H:%M")

    payload = {
        "student_name": resp.usuario.nombre if resp.usuario else "Estudiante",
        "student_doc": resp.usuario.numero_documento if resp.usuario else "N/A",
        "institution_name": resp.institucion.nombre if resp.institucion else "N/A",
        "group_name": (resp.usuario.grupo.nombre if resp.usuario and resp.usuario.grupo else "N/A"),
        "simulacro_title": resp.simulacro.titulo if resp.simulacro else "Simulacro",
        "area_display": area_display,
        "score_100": round(score, 1),
        "generated_at": generated_at,
        "report_markdown": informe,
    }

    buffer = io.BytesIO()
    PDFReportService.generate_individual_ai_report(buffer, payload)
    buffer.seek(0)

    safe_student = _safe_filename_part(payload["student_name"], "Estudiante")
    safe_area = _safe_filename_part(area_display.replace(" ", "_"), "Area")
    filename = f"Informe_IA_{safe_student}_{safe_area}.pdf"

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/lista/{tipo_reporte}", response_model=List[ReporteItem])
def get_reportes_lista(
    tipo_reporte: str,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Lista histórica de reportes filtrada por tipo.
    """
    inst_id = current_user.institucion_id
    if current_user.rol.nombre not in ['admin', 'docente']:
        raise HTTPException(status_code=403, detail="No tiene permisos.")
    
    items = []
    
    # 1. INDIVIDUAL
    if tipo_reporte == "individual":
        q = db.query(RespuestaEstudiante).filter(
            RespuestaEstudiante.analisis_ia != None,
            RespuestaEstudiante.anulado.is_(False)
        )
        if inst_id: q = q.filter(RespuestaEstudiante.institucion_id == inst_id)

        q = q.join(Simulacro)

        # Eager load
        q = q.options(joinedload(RespuestaEstudiante.simulacro))

        q = q.order_by(RespuestaEstudiante.updated_at.desc())

        results = q.offset(offset).limit(limit).all()

        for r in results:
            titulo = r.simulacro.area
            tags = [titulo[:3].upper()]

            items.append(ReporteItem(
                id=r.id,
                titulo=titulo,
                subtitulo=f"{r.usuario.nombre} - {r.simulacro.titulo}",
                fecha=r.updated_at or r.created_at,
                puntaje=float(r.puntaje_total) if r.puntaje_total is not None else 0,
                tags=tags,
                metadata={"usuario_id": r.usuario_id, "simulacro_id": r.simulacro_id},
                tipo_reporte="individual",
                fraude=r.fraude # Mapear valor
            ))

    # 2. GRUPAL
    elif tipo_reporte == "grupal":
        q = db.query(ReporteGrupal).join(Simulacro).filter(ReporteGrupal.anulado.is_(False))
        if inst_id: q = q.filter(ReporteGrupal.institucion_id == inst_id)

        q = q.options(joinedload(ReporteGrupal.simulacro))
        q = q.order_by(ReporteGrupal.created_at.desc())

        results = q.offset(offset).limit(limit).all()

        for g in results:
            tags = ["GRUPAL"]

            items.append(ReporteItem(
                id=g.id,
                titulo=f"Grupal: {g.simulacro.area}",
                subtitulo=g.simulacro.titulo,
                fecha=g.created_at,
                tags=tags,
                metadata={"simulacro_id": g.simulacro_id},
                tipo_reporte="grupal"
            ))
            
    return items
