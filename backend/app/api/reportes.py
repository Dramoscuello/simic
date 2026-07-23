import io
import re

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

class AreaItem(BaseModel):
    area: str
    display: str
    score: Optional[float] = None
    respuesta_id: int
    fraude: bool = False

class ReporteItem(BaseModel):
    id: int # ID del reporte o respuesta (o clave hash para batch)
    titulo: str
    subtitulo: str
    fecha: datetime
    puntaje: Optional[float] = None
    tags: List[str] = []
    areas: Optional[List[AreaItem]] = None  # Solo para reportes agrupados (individual_batch, grupal_batch)
    puntaje_global: Optional[float] = None  # Solo para reportes agrupados
    metadata: Dict[str, Any] = {} # IDs relacionados (usuario_id, simulacro_id, etc)
    tipo_reporte: str # "individual", "grupal", "individual_batch", "grupal_batch"
    fraude: bool = False

class DashboardData(BaseModel):
    stats: DashboardStats
    individuales: List[ReporteItem]
    grupales: List[ReporteItem]

def _get_grupal_batch_items(db: Session, inst_id: Optional[int] = None) -> List[ReporteItem]:
    sim_q = db.query(Simulacro).filter(
        Simulacro.batch_id.isnot(None)
    )
    if inst_id:
        sim_q = sim_q.filter(Simulacro.institucion_id == inst_id)

    simulacros = sim_q.all()
    if not simulacros:
        return []

    batch_map = {}
    for s in simulacros:
        batch_map.setdefault(s.batch_id, []).append(s)

    items = []
    PESOS_GLOBAL = {
        "LECTURA_CRITICA": 3, "MATEMATICAS": 3,
        "SOCIALES_CIUDADANAS": 3, "CIENCIAS_NATURALES": 3, "INGLES": 1
    }
    PESO_TOTAL = 13.0

    for bid, sims in batch_map.items():
        sim_ids = [s.id for s in sims]
        sim_area_map = {s.id: s.area for s in sims}

        resp_q = db.query(RespuestaEstudiante).filter(
            RespuestaEstudiante.simulacro_id.in_(sim_ids),
            RespuestaEstudiante.anulado.is_(False)
        )
        if inst_id:
            resp_q = resp_q.filter(RespuestaEstudiante.institucion_id == inst_id)

        respuestas = resp_q.all()
        if not respuestas:
            continue

        area_scores = {}
        latest_date = None

        for r in respuestas:
            area = sim_area_map.get(r.simulacro_id)
            if not area:
                continue
            score = float(r.puntaje_total) if r.puntaje_total is not None else 0.0
            area_scores.setdefault(area, []).append(score)
            r_date = r.updated_at or r.created_at
            if latest_date is None or (r_date and r_date > latest_date):
                latest_date = r_date

        areas_items = []
        suma_ponderada = 0.0
        for area_code, scores in area_scores.items():
            avg_area = sum(scores) / len(scores) if scores else 0.0
            area_display = AREA_DISPLAY_MAP.get(area_code, area_code.replace("_", " ").title())
            areas_items.append(AreaItem(
                area=area_code,
                display=area_display,
                score=round(avg_area, 1),
                respuesta_id=sims[0].id,
                fraude=False
            ))
            peso = PESOS_GLOBAL.get(area_code, 3)
            suma_ponderada += avg_area * peso

        puntaje_global = round((suma_ponderada / PESO_TOTAL) * 5.0, 1) if suma_ponderada > 0 else None

        sample_titulo = sims[0].titulo if sims else bid
        m = re.match(r'^(.*?)\s*-\s*(Matemáticas|Lectura Crítica|Ciencias Naturales|Sociales y Ciudadanas|Inglés)', sample_titulo)
        titulo_base = m.group(1).strip() if m else sample_titulo

        items.append(ReporteItem(
            id=abs(hash(bid)) % (10 ** 8),
            titulo=f"Diagnóstico grupal: {len(sims)} áreas",
            subtitulo=titulo_base,
            fecha=latest_date or sims[0].created_at or datetime.now(),
            puntaje_global=puntaje_global,
            tags=["GRUPAL", "BATCH", f"{len(sims)} áreas"],
            areas=areas_items,
            metadata={
                "batch_id": bid,
                "institucion_id": inst_id or sims[0].institucion_id,
                "simulacro_ids": sim_ids,
            },
            tipo_reporte="grupal_batch"
        ))

    items.sort(key=lambda x: x.fecha, reverse=True)
    return items


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
        raise HTTPException(status_code=403, detail="No tiene permisos para ver el dashboard institucional.")
    
    inst_id = current_user.institucion_id
    sede_id = current_user.sede_id if current_user.rol.nombre == 'docente' else None
    
    from app.models.usuario import Usuario as UserModel
    def _scope_r(query):
        if sede_id:
            return query.join(UserModel, UserModel.id == RespuestaEstudiante.usuario_id)\
                        .filter(UserModel.sede_id == sede_id)
        return query

    # 1. STATS (Cálculo rápido)
    q_est = db.query(RespuestaEstudiante.usuario_id).distinct().filter(RespuestaEstudiante.anulado.is_(False))
    if inst_id:
        q_est = q_est.filter(RespuestaEstudiante.institucion_id == inst_id)
    q_est = _scope_r(q_est) if sede_id else q_est
    total_estudiantes = q_est.count()
    
    q_sims = db.query(RespuestaEstudiante).filter(RespuestaEstudiante.anulado.is_(False))
    if inst_id:
        q_sims = q_sims.filter(RespuestaEstudiante.institucion_id == inst_id)
    q_sims = _scope_r(q_sims) if sede_id else q_sims
    total_simulacros = q_sims.count()
    
    from sqlalchemy import func
    avg_score = db.query(func.avg(RespuestaEstudiante.puntaje_total)).filter(RespuestaEstudiante.anulado.is_(False))
    if inst_id:
        avg_score = avg_score.filter(RespuestaEstudiante.institucion_id == inst_id)
    avg_score = _scope_r(avg_score) if sede_id else avg_score
    promedio = avg_score.scalar() or 0.0

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

    # 2. REPORTES INDIVIDUALES — Agrupados por batch+estudiante
    q_ind = db.query(RespuestaEstudiante).options(
        joinedload(RespuestaEstudiante.simulacro),
        joinedload(RespuestaEstudiante.usuario)
    ).filter(
        RespuestaEstudiante.puntaje_total != None,
        RespuestaEstudiante.anulado.is_(False)
    )
    if inst_id:
        q_ind = q_ind.filter(RespuestaEstudiante.institucion_id == inst_id)
    q_ind = _scope_r(q_ind) if sede_id else q_ind

    individuales_db = q_ind.order_by(RespuestaEstudiante.updated_at.desc()).limit(50).all()

    PESOS_GLOBAL = {
        "LECTURA_CRITICA": 3, "MATEMATICAS": 3,
        "SOCIALES_CIUDADANAS": 3, "CIENCIAS_NATURALES": 3, "INGLES": 1
    }
    PESO_TOTAL = 13.0

    grouped = {}
    order_keys = []

    for r in individuales_db:
        batch_id = r.simulacro.batch_id if r.simulacro else None
        uid = r.usuario_id
        group_key = (batch_id or f"sim_{r.simulacro_id}", uid)

        if group_key not in grouped:
            grouped[group_key] = {
                "student_name": r.usuario.nombre if r.usuario else "Estudiante",
                "usuario_id": uid,
                "batch_id": batch_id,
                "simulacro_ids": [r.simulacro_id],
                "titulo_base": "",
                "fecha": r.updated_at or r.created_at,
                "areas": [],
                "has_fraude": False,
            }
            order_keys.append(group_key)

        entry = grouped[group_key]
        entry["simulacro_ids"].append(r.simulacro_id)
        if r.fraude:
            entry["has_fraude"] = True

        area_code = r.simulacro.area if r.simulacro else "DESCONOCIDO"
        area_display = AREA_DISPLAY_MAP.get(area_code, area_code.replace("_", " ").title())

        entry["areas"].append({
            "area": area_code,
            "display": area_display,
            "score": float(r.puntaje_total) if r.puntaje_total is not None else 0,
            "respuesta_id": r.id,
            "fraude": r.fraude,
        })

        if r.updated_at and (not entry["fecha"] or r.updated_at > entry["fecha"]):
            entry["fecha"] = r.updated_at

        titulo_base = r.simulacro.titulo if r.simulacro else ""
        m = re.match(r'^(.*?)\s*-\s*(Matemáticas|Lectura Crítica|Ciencias Naturales|Sociales y Ciudadanas|Inglés)', titulo_base)
        if m:
            entry["titulo_base"] = m.group(1).strip()
        elif not entry["titulo_base"]:
            entry["titulo_base"] = titulo_base

    individuales = []
    for gk in order_keys:
        entry = grouped[gk]
        dedup_areas = {}
        for a in entry["areas"]:
            key = a["area"]
            if key not in dedup_areas or a["fraude"] is False:
                dedup_areas[key] = a
        areas_final = sorted(dedup_areas.values(), key=lambda a: a["area"])

        tags = [a["area"][:3].upper() for a in areas_final]

        suma_ponderada = 0.0
        for a in areas_final:
            peso = PESOS_GLOBAL.get(a["area"], 3)
            suma_ponderada += (a["score"] or 0) * peso
        puntaje_global = (suma_ponderada / PESO_TOTAL) * 5

        batch_key_id = abs(hash(str(gk))) % (10 ** 8)

        individuales.append(ReporteItem(
            id=batch_key_id,
            titulo=entry["student_name"],
            subtitulo=entry["titulo_base"] or "Simulacro",
            fecha=entry["fecha"] or datetime.now(),
            puntaje=round(float(puntaje_global), 2),
            tags=tags,
            areas=[AreaItem(**a) for a in areas_final],
            puntaje_global=round(float(puntaje_global), 2),
            metadata={
                "usuario_id": entry["usuario_id"],
                "batch_id": entry["batch_id"],
                "simulacro_ids": list(set(entry["simulacro_ids"])),
            },
            tipo_reporte="individual_batch",
            fraude=entry["has_fraude"],
        ))

        if len(individuales) >= 5:
            break

    # 3. REPORTES GRUPALES
    grupales = _get_grupal_batch_items(db, inst_id)[:5]

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

class ReporteBatchArea(BaseModel):
    area: str
    display: str
    score: Optional[float] = None
    respuesta_id: int
    contenido: Optional[str] = None
    fraude: bool = False

class ReporteBatchDetalle(BaseModel):
    titulo: str
    subtitulo: str
    fecha: datetime
    areas: List[ReporteBatchArea]
    puntaje_global: Optional[float] = None

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


@router.get("/detalle/individual-batch", response_model=ReporteBatchDetalle)
def get_reporte_batch_detalle(
    usuario_id: int = Query(...),
    batch_id: Optional[str] = Query(None),
    simulacro_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user),
):
    """Retorna todos los informes IA de un estudiante para un batch (o simulacro suelto) con tabs por área."""
    if current_user.rol.nombre not in ['admin', 'docente']:
        raise HTTPException(status_code=403, detail="No tiene permisos.")

    if not batch_id and not simulacro_id:
        raise HTTPException(status_code=400, detail="Se requiere batch_id o simulacro_id")

    inst_id = current_user.institucion_id
    if not inst_id:
        raise HTTPException(status_code=400, detail="Usuario sin institución asignada")

    q = db.query(RespuestaEstudiante).options(
        joinedload(RespuestaEstudiante.simulacro),
        joinedload(RespuestaEstudiante.usuario),
    ).filter(
        RespuestaEstudiante.usuario_id == usuario_id,
        RespuestaEstudiante.institucion_id == inst_id,
        RespuestaEstudiante.anulado.is_(False),
        RespuestaEstudiante.analisis_ia != None,
    )

    if batch_id:
        q = q.join(Simulacro).filter(Simulacro.batch_id == batch_id).order_by(Simulacro.area)
    else:
        q = q.filter(RespuestaEstudiante.simulacro_id == simulacro_id)

    respuestas = q.all()

    if not respuestas:
        raise HTTPException(status_code=404, detail="No se encontraron reportes para este batch")

    student_name = respuestas[0].usuario.nombre if respuestas[0].usuario else "Estudiante"
    titulo_base = ""
    m = re.match(r'^(.*?)\s*-\s*(Matemáticas|Lectura Crítica|Ciencias Naturales|Sociales y Ciudadanas|Inglés)',
                 respuestas[0].simulacro.titulo if respuestas[0].simulacro else "")
    if m:
        titulo_base = m.group(1).strip()
    else:
        titulo_base = respuestas[0].simulacro.titulo if respuestas[0].simulacro else "Simulacro"

    PESOS_GLOBAL = {
        "LECTURA_CRITICA": 3, "MATEMATICAS": 3,
        "SOCIALES_CIUDADANAS": 3, "CIENCIAS_NATURALES": 3, "INGLES": 1
    }
    PESO_TOTAL = 13.0

    areas = []
    suma_ponderada = 0.0
    for r in respuestas:
        area_code = r.simulacro.area if r.simulacro else "DESCONOCIDO"
        area_display = AREA_DISPLAY_MAP.get(area_code, area_code.replace("_", " ").title())
        analisis = r.analisis_ia or {}
        informe = analisis.get("informe_ia") or "Contenido no disponible."
        score = float(r.puntaje_total) if r.puntaje_total is not None else 0

        areas.append(ReporteBatchArea(
            area=area_code,
            display=area_display,
            score=round(score, 2),
            respuesta_id=r.id,
            contenido=informe,
            fraude=r.fraude,
        ))
        peso = PESOS_GLOBAL.get(area_code, 3)
        suma_ponderada += score * peso

    puntaje_global = round((suma_ponderada / PESO_TOTAL) * 5, 2)

    return ReporteBatchDetalle(
        titulo=f"Reporte: {student_name}",
        subtitulo=titulo_base,
        fecha=respuestas[0].updated_at or respuestas[0].created_at or datetime.now(),
        areas=areas,
        puntaje_global=puntaje_global,
    )


from app.models.institucion import Institucion

class GrupalBatchAreaItem(BaseModel):
    area: str
    display: str
    reporte_grupal_id: int
    average_score_100: Optional[float] = None
    students_count: Optional[int] = None
    performance_level: Optional[str] = None

class EstudianteBatchItem(BaseModel):
    usuario_id: int
    numero_documento: str
    nombre: str
    lectura_critica: float
    matematicas: float
    ciencias_naturales: float
    sociales_ciudadanas: float
    ingles: float
    puntaje_total: float

class GrupalBatchDetalle(BaseModel):
    batch_id: str
    institucion_nombre: str
    titulo: str
    subtitulo: str
    fecha: datetime
    areas: List[GrupalBatchAreaItem]
    puntaje_global: Optional[float] = None
    estudiantes: List[EstudianteBatchItem] = []
    total_estudiantes_completos: int = 0


def get_batch_estudiantes_completos(db: Session, batch_id: str, inst_id: Optional[int] = None) -> List[Dict]:
    sim_q = db.query(Simulacro).filter(Simulacro.batch_id == batch_id)
    if inst_id:
        sim_q = sim_q.filter(Simulacro.institucion_id == inst_id)
    simulacros = sim_q.all()

    if not simulacros:
        return []

    sim_map = {s.id: s.area for s in simulacros}
    sim_ids = list(sim_map.keys())

    resp_q = db.query(RespuestaEstudiante).options(
        joinedload(RespuestaEstudiante.usuario)
    ).filter(
        RespuestaEstudiante.simulacro_id.in_(sim_ids),
        RespuestaEstudiante.anulado.is_(False)
    )
    if inst_id:
        resp_q = resp_q.filter(RespuestaEstudiante.institucion_id == inst_id)

    respuestas = resp_q.all()

    def _std_area(area_str: str) -> str:
        a = (area_str or "").upper()
        if "MAT" in a: return "MATEMATICAS"
        if "LECT" in a: return "LECTURA_CRITICA"
        if "SOC" in a: return "SOCIALES_CIUDADANAS"
        if "CIEN" in a or "NAT" in a: return "CIENCIAS_NATURALES"
        if "ING" in a: return "INGLES"
        return a

    user_scores = {}
    user_objs = {}

    for r in respuestas:
        if not r.usuario:
            continue
        uid = r.usuario_id
        area_raw = sim_map.get(r.simulacro_id, "")
        area_code = _std_area(area_raw)

        if uid not in user_scores:
            user_scores[uid] = {}
            user_objs[uid] = r.usuario

        score = float(r.puntaje_total) if r.puntaje_total is not None else 0.0
        user_scores[uid][area_code] = score

    REQUERIDAS = {"MATEMATICAS", "LECTURA_CRITICA", "CIENCIAS_NATURALES", "SOCIALES_CIUDADANAS", "INGLES"}
    PESO_TOTAL = 13.0

    completos = []
    for uid, scores in user_scores.items():
        if len(REQUERIDAS.intersection(scores.keys())) == 5:
            u = user_objs[uid]
            lc = scores.get("LECTURA_CRITICA", 0.0)
            mat = scores.get("MATEMATICAS", 0.0)
            cn = scores.get("CIENCIAS_NATURALES", 0.0)
            soc = scores.get("SOCIALES_CIUDADANAS", 0.0)
            ing = scores.get("INGLES", 0.0)

            suma_ponderada = (3 * lc) + (3 * mat) + (3 * cn) + (3 * soc) + (1 * ing)
            puntaje_global_500 = round((suma_ponderada / PESO_TOTAL) * 5.0, 1)

            completos.append({
                "usuario_id": uid,
                "numero_documento": u.numero_documento or "N/A",
                "nombre": u.nombre or "Estudiante",
                "lectura_critica": round(lc, 1),
                "matematicas": round(mat, 1),
                "ciencias_naturales": round(cn, 1),
                "sociales_ciudadanas": round(soc, 1),
                "ingles": round(ing, 1),
                "puntaje_total": puntaje_global_500,
            })

    completos.sort(key=lambda x: x["puntaje_total"], reverse=True)
    return completos


@router.get("/detalle/grupal-batch", response_model=GrupalBatchDetalle)
def get_reporte_grupal_batch_detalle(
    batch_id: str = Query(...),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user),
):
    """Retorna el detalle agrupado de reportes grupales para un batch (multi-área) con la lista de estudiantes."""
    if current_user.rol.nombre not in ['admin', 'docente']:
        raise HTTPException(status_code=403, detail="No tiene permisos.")

    inst_id = current_user.institucion_id
    inst_name = "Institución Educativa"
    if inst_id:
        inst_obj = db.query(Institucion).filter(Institucion.id == inst_id).first()
        if inst_obj:
            inst_name = inst_obj.nombre
    else:
        sample_sim = db.query(Simulacro).filter(Simulacro.batch_id == batch_id).first()
        if sample_sim and sample_sim.institucion_id:
            inst_obj = db.query(Institucion).filter(Institucion.id == sample_sim.institucion_id).first()
            if inst_obj:
                inst_name = inst_obj.nombre
                inst_id = inst_obj.id

    sim_q = db.query(Simulacro).filter(
        Simulacro.batch_id == batch_id
    )
    if inst_id:
        sim_q = sim_q.filter(Simulacro.institucion_id == inst_id)
    
    simulacros_list = sim_q.order_by(Simulacro.area).all()

    if not simulacros_list:
        raise HTTPException(status_code=404, detail="No se encontraron simulacros para este batch.")

    reportes_grupales = db.query(ReporteGrupal).filter(
        ReporteGrupal.simulacro_id.in_([s.id for s in simulacros_list]),
        ReporteGrupal.anulado.is_(False)
    ).all()
    rg_map = {rg.simulacro_id: rg for rg in reportes_grupales}

    PESOS_GLOBAL = {
        "LECTURA_CRITICA": 3, "MATEMATICAS": 3,
        "SOCIALES_CIUDADANAS": 3, "CIENCIAS_NATURALES": 3, "INGLES": 1
    }
    PESO_TOTAL = 13.0

    areas = []
    suma_ponderada = 0.0
    latest_date = None

    for sim in simulacros_list:
        area_code = sim.area
        area_display = AREA_DISPLAY_MAP.get(area_code, area_code.replace("_", " ").title())
        
        resp_q = db.query(RespuestaEstudiante).filter(
            RespuestaEstudiante.simulacro_id == sim.id,
            RespuestaEstudiante.anulado.is_(False)
        )
        if inst_id:
            resp_q = resp_q.filter(RespuestaEstudiante.institucion_id == inst_id)
        
        resps = resp_q.all()
        scores = [float(r.puntaje_total) for r in resps if r.puntaje_total is not None]
        avg_score = (sum(scores) / len(scores)) if scores else None
        students_count = len(scores)

        rg = rg_map.get(sim.id)
        stats = rg.estadisticas_agregadas if rg else {}
        perf_level = stats.get("performance_level")

        areas.append(GrupalBatchAreaItem(
            area=area_code,
            display=area_display,
            reporte_grupal_id=rg.id if rg else sim.id,
            average_score_100=round(avg_score, 1) if avg_score is not None else None,
            students_count=students_count,
            performance_level=perf_level,
        ))

        if avg_score is not None:
            peso = PESOS_GLOBAL.get(area_code, 3)
            suma_ponderada += float(avg_score) * peso

        s_date = sim.created_at
        if latest_date is None or (s_date and s_date > latest_date):
            latest_date = s_date

    puntaje_global = round((suma_ponderada / PESO_TOTAL) * 5.0, 1) if suma_ponderada > 0 else None

    sample_titulo = simulacros_list[0].titulo if simulacros_list else batch_id
    m = re.match(r'^(.*?)\s*-\s*(Matemáticas|Lectura Crítica|Ciencias Naturales|Sociales y Ciudadanas|Inglés)', sample_titulo)
    titulo_base = m.group(1).strip() if m else sample_titulo

    estudiantes_completos = get_batch_estudiantes_completos(db, batch_id, inst_id)

    return GrupalBatchDetalle(
        batch_id=batch_id,
        institucion_nombre=inst_name,
        titulo=f"Diagnóstico grupal: {len(simulacros_list)} áreas",
        subtitulo=titulo_base,
        fecha=latest_date or datetime.now(),
        areas=areas,
        puntaje_global=puntaje_global,
        estudiantes=[EstudianteBatchItem(**e) for e in estudiantes_completos],
        total_estudiantes_completos=len(estudiantes_completos),
    )


@router.get("/grupal-batch/{batch_id}/pdf")
def get_reporte_grupal_batch_pdf(
    batch_id: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Genera y descarga el informe PDF profesional usando ReportLab para el diagnóstico grupal por lote (5 áreas).
    """
    if current_user.rol.nombre not in ['admin', 'docente']:
        raise HTTPException(status_code=403, detail="No tiene permisos para descargar este informe.")

    inst_id = current_user.institucion_id

    institucion_nombre = "Institución Educativa"
    if inst_id:
        inst_obj = db.query(Institucion).filter(Institucion.id == inst_id).first()
        if inst_obj:
            institucion_nombre = inst_obj.nombre
    else:
        sample_sim = db.query(Simulacro).filter(Simulacro.batch_id == batch_id).first()
        if sample_sim and sample_sim.institucion_id:
            inst_obj = db.query(Institucion).filter(Institucion.id == sample_sim.institucion_id).first()
            if inst_obj:
                institucion_nombre = inst_obj.nombre
                inst_id = inst_obj.id

    sim_q = db.query(Simulacro).filter(
        Simulacro.batch_id == batch_id
    )
    if inst_id:
        sim_q = sim_q.filter(Simulacro.institucion_id == inst_id)

    rep_rows = sim_q.all()
    if not rep_rows:
        raise HTTPException(status_code=404, detail="No se encontraron simulacros para este batch.")

    sample_titulo = rep_rows[0].titulo if rep_rows[0].titulo else batch_id
    m = re.match(r'^(.*?)\s*-\s*(Matemáticas|Lectura Crítica|Ciencias Naturales|Sociales y Ciudadanas|Inglés)', sample_titulo)
    titulo_base = m.group(1).strip() if m else sample_titulo

    estudiantes_completos = get_batch_estudiantes_completos(db, batch_id, inst_id)

    promedios = {}
    if estudiantes_completos:
        promedios["Lectura Crítica"] = round(sum(e["lectura_critica"] for e in estudiantes_completos) / len(estudiantes_completos), 1)
        promedios["Matemáticas"] = round(sum(e["matematicas"] for e in estudiantes_completos) / len(estudiantes_completos), 1)
        promedios["Ciencias Naturales"] = round(sum(e["ciencias_naturales"] for e in estudiantes_completos) / len(estudiantes_completos), 1)
        promedios["Sociales y C."] = round(sum(e["sociales_ciudadanas"] for e in estudiantes_completos) / len(estudiantes_completos), 1)
        promedios["Inglés"] = round(sum(e["ingles"] for e in estudiantes_completos) / len(estudiantes_completos), 1)

    avg_global = round(sum(e["puntaje_total"] for e in estudiantes_completos) / len(estudiantes_completos), 1) if estudiantes_completos else 0.0

    pdf_data = {
        "institution_name": institucion_nombre,
        "batch_id": batch_id,
        "titulo_base": titulo_base,
        "total_estudiantes": len(estudiantes_completos),
        "promedio_global_500": avg_global,
        "promedios_por_area": promedios,
        "estudiantes": estudiantes_completos,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }

    buffer = io.BytesIO()
    PDFReportService.generate_grupal_batch_pdf(buffer, pdf_data)
    buffer.seek(0)

    safe_title = _safe_filename_part(titulo_base, "Batch")
    filename = f"Reporte_Grupal_Batch_{safe_title}.pdf"

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/detalle/{tipo_reporte}/{id}/pdf")
def get_reporte_detalle_pdf(
    tipo_reporte: str,
    id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Descarga PDF de alta calidad desde el backend para reporte individual por área.
    """
    inst_id = current_user.institucion_id
    if current_user.rol.nombre not in ["admin", "docente"]:
        raise HTTPException(status_code=403, detail="No tiene permisos.")

    if tipo_reporte not in ["individual", "individual_batch"]:
        raise HTTPException(status_code=400, detail="Endpoint reservado para descarga de reportes individuales.")

    resp = db.query(RespuestaEstudiante).options(
        joinedload(RespuestaEstudiante.usuario).joinedload(Usuario.grupo),
        joinedload(RespuestaEstudiante.institucion),
        joinedload(RespuestaEstudiante.simulacro),
    ).filter(RespuestaEstudiante.id == id).first()

    if not resp or resp.anulado:
        raise HTTPException(status_code=404, detail="Reporte no encontrado.")

    if current_user.rol.nombre != "admin" and resp.institucion_id != inst_id:
        raise HTTPException(status_code=403, detail="No autorizado (pertenece a otra institución).")

    if resp.fraude:
        raise HTTPException(status_code=400, detail="El informe no está disponible para intentos con fraude.")

    analisis = resp.analisis_ia or {}
    informe = analisis.get("informe_ia")
    if not informe or not str(informe).strip():
        score_val = float(resp.puntaje_total) if resp.puntaje_total is not None else 0.0
        area_name = resp.simulacro.area if resp.simulacro else "N/A"
        area_name = AREA_DISPLAY_MAP.get(area_name, area_name)
        informe = (
            f"### Resumen de Evaluación\n\n"
            f"El estudiante **{resp.usuario.nombre if resp.usuario else 'Estudiante'}** ha completado el examen del área de **{area_name}** "
            f"obteniendo un puntaje de **{score_val:.1f} / 100**.\n\n"
            f"El análisis cualitativo detallado por inteligencia artificial puede ser generado desde el panel de revisión."
        )

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
    filename = f"Reporte_Individual_{safe_student}_{safe_area}.pdf"

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
        sede_id = current_user.sede_id if current_user.rol.nombre == 'docente' else None
        from app.models.usuario import Usuario as UserModel
        def _scope_r(query):
            if sede_id:
                return query.join(UserModel, UserModel.id == RespuestaEstudiante.usuario_id)\
                            .filter(UserModel.sede_id == sede_id)
            return query

        q = db.query(RespuestaEstudiante).options(
            joinedload(RespuestaEstudiante.simulacro),
            joinedload(RespuestaEstudiante.usuario)
        ).filter(
            RespuestaEstudiante.puntaje_total != None,
            RespuestaEstudiante.anulado.is_(False)
        )
        if inst_id:
            q = q.filter(RespuestaEstudiante.institucion_id == inst_id)
        q = _scope_r(q)

        results = q.order_by(RespuestaEstudiante.updated_at.desc()).limit(1000).all()

        PESOS_GLOBAL = {
            "LECTURA_CRITICA": 3, "MATEMATICAS": 3,
            "SOCIALES_CIUDADANAS": 3, "CIENCIAS_NATURALES": 3, "INGLES": 1
        }
        PESO_TOTAL = 13.0

        grouped = {}  # key: (batch_id or simulacro_id, usuario_id)
        order_keys = []

        for r in results:
            batch_id = r.simulacro.batch_id if r.simulacro else None
            uid = r.usuario_id
            group_key = (batch_id or f"sim_{r.simulacro_id}", uid)

            if group_key not in grouped:
                grouped[group_key] = {
                    "student_name": r.usuario.nombre if r.usuario else "Estudiante",
                    "usuario_id": uid,
                    "batch_id": batch_id,
                    "simulacro_ids": [r.simulacro_id],
                    "titulo_base": "",
                    "fecha": r.updated_at or r.created_at,
                    "areas": [],
                    "has_fraude": False,
                }
                order_keys.append(group_key)

            entry = grouped[group_key]
            entry["simulacro_ids"].append(r.simulacro_id)
            if r.fraude:
                entry["has_fraude"] = True

            area_code = r.simulacro.area if r.simulacro else "DESCONOCIDO"
            area_display = AREA_DISPLAY_MAP.get(area_code, area_code.replace("_", " ").title())

            entry["areas"].append({
                "area": area_code,
                "display": area_display,
                "score": float(r.puntaje_total) if r.puntaje_total is not None else 0,
                "respuesta_id": r.id,
                "fraude": r.fraude,
            })

            if r.updated_at and (not entry["fecha"] or r.updated_at > entry["fecha"]):
                entry["fecha"] = r.updated_at

            titulo_base = r.simulacro.titulo if r.simulacro else ""
            m = re.match(r'^(.*?)\s*-\s*(Matemáticas|Lectura Crítica|Ciencias Naturales|Sociales y Ciudadanas|Inglés)', titulo_base)
            if m:
                entry["titulo_base"] = m.group(1).strip()
            elif not entry["titulo_base"]:
                entry["titulo_base"] = titulo_base

        individuales = []
        for gk in order_keys:
            entry = grouped[gk]
            dedup_areas = {}
            for a in entry["areas"]:
                key = a["area"]
                if key not in dedup_areas or a["fraude"] is False:
                    dedup_areas[key] = a
            areas_final = sorted(dedup_areas.values(), key=lambda a: a["area"])

            tags = [a["area"][:3].upper() for a in areas_final]

            suma_ponderada = 0.0
            for a in areas_final:
                peso = PESOS_GLOBAL.get(a["area"], 3)
                suma_ponderada += (a["score"] or 0) * peso
            puntaje_global = (suma_ponderada / PESO_TOTAL) * 5

            batch_key_id = abs(hash(str(gk))) % (10 ** 8)

            individuales.append(ReporteItem(
                id=batch_key_id,
                titulo=entry["student_name"],
                subtitulo=entry["titulo_base"] or "Simulacro",
                fecha=entry["fecha"] or datetime.now(),
                puntaje=round(float(puntaje_global), 2),
                tags=tags,
                areas=[AreaItem(**a) for a in areas_final],
                puntaje_global=round(float(puntaje_global), 2),
                metadata={
                    "usuario_id": entry["usuario_id"],
                    "batch_id": entry["batch_id"],
                    "simulacro_ids": list(set(entry["simulacro_ids"])),
                },
                tipo_reporte="individual_batch",
                fraude=entry["has_fraude"],
            ))

        items = individuales[offset : offset + limit]

    # 2. GRUPAL
    elif tipo_reporte == "grupal":
        all_grupales = _get_grupal_batch_items(db, inst_id)
        items = all_grupales[offset : offset + limit]

    return items
