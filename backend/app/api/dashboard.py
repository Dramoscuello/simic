"""
Dashboard API - Endpoints para métricas de gestión operativa.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, case, extract
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel

from app.database.config import get_db
from app.models.institucion import Institucion
from app.models.usuario import Usuario
from app.models.simulacro import Simulacro
from app.models.respuesta_estudiante import RespuestaEstudiante
from app.models.rol import Rol
from app.api.deps import get_current_active_user

# Constantes para las áreas ICFES
AREA_CODIGOS = {
    "MATEMATICAS": "MAT",
    "Matemáticas": "MAT",
    "LECTURA_CRITICA": "LC",
    "Lectura Crítica": "LC",
    "CIENCIAS_NATURALES": "CN",
    "Ciencias Naturales": "CN",
    "SOCIALES_CIUDADANAS": "SOC",
    "Ciencias Sociales": "SOC",
    "INGLES": "ING",
    "Inglés": "ING",
}

AREA_COLORS = {
    "MATEMATICAS": "#6366f1",  # indigo
    "Matemáticas": "#6366f1",
    "LECTURA_CRITICA": "#8b5cf6",  # violet
    "Lectura Crítica": "#8b5cf6",
    "CIENCIAS_NATURALES": "#10b981",  # emerald
    "Ciencias Naturales": "#10b981",
    "SOCIALES_CIUDADANAS": "#f59e0b",  # amber
    "Ciencias Sociales": "#f59e0b",
    "INGLES": "#ec4899",  # pink
    "Inglés": "#ec4899",
}

# Rangos oficiales ICFES Saber 11 por área
# Formato: lista de tuplas (limite_superior, nombre_nivel)
RANGOS_ICFES_POR_AREA = {
    "MATEMATICAS": [
        (35, "Nivel 1"),
        (50, "Nivel 2"),
        (70, "Nivel 3"),
        (100, "Nivel 4"),
    ],
    "LECTURA_CRITICA": [
        (35, "Nivel 1"),
        (50, "Nivel 2"),
        (65, "Nivel 3"),
        (100, "Nivel 4"),
    ],
    "CIENCIAS_NATURALES": [
        (40, "Nivel 1"),
        (55, "Nivel 2"),
        (70, "Nivel 3"),
        (100, "Nivel 4"),
    ],
    "SOCIALES_CIUDADANAS": [
        (40, "Nivel 1"),
        (55, "Nivel 2"),
        (70, "Nivel 3"),
        (100, "Nivel 4"),
    ],
    "INGLES": [
        (36, "Pre A1"),
        (57, "A1"),
        (70, "A2"),
        (100, "B1"),
    ],
}

# Mapeo de nombres alternativos a nombres canónicos
AREA_CANONICAL = {
    "MATEMATICAS": "MATEMATICAS",
    "Matemáticas": "MATEMATICAS",
    "LECTURA_CRITICA": "LECTURA_CRITICA",
    "Lectura Crítica": "LECTURA_CRITICA",
    "CIENCIAS_NATURALES": "CIENCIAS_NATURALES",
    "Ciencias Naturales": "CIENCIAS_NATURALES",
    "SOCIALES_CIUDADANAS": "SOCIALES_CIUDADANAS",
    "Ciencias Sociales": "SOCIALES_CIUDADANAS",
    "INGLES": "INGLES",
    "Inglés": "INGLES",
}


def get_nivel_icfes(area: str, puntaje: float) -> tuple:
    """
    Clasifica un puntaje según los rangos oficiales ICFES del área.
    Retorna (nombre_nivel, indice_nivel) donde indice va de 0 a 3.
    """
    area_canonical = AREA_CANONICAL.get(area, area)
    rangos = RANGOS_ICFES_POR_AREA.get(area_canonical)
    
    if not rangos:
        # Fallback a rangos genéricos si no se encuentra el área
        rangos = [(35, "Nivel 1"), (55, "Nivel 2"), (70, "Nivel 3"), (100, "Nivel 4")]
    
    for idx, (limite, nombre) in enumerate(rangos):
        if puntaje <= limite:
            return nombre, idx
    
    # Si supera todos los límites, retornar el último nivel
    return rangos[-1][1], len(rangos) - 1


router = APIRouter(
    prefix="/dashboard",
    tags=["dashboard"]
)


# ==========================================
# SCHEMAS
# ==========================================

class KPICard(BaseModel):
    """Estructura de una tarjeta KPI"""
    label: str
    value: int
    change_value: Optional[str] = None
    change_type: str = "neutral"  # "up", "down", "neutral", "new"
    change_label: str = ""


class ProduccionSemanal(BaseModel):
    """Datos de producción para gráfico de barras"""
    dia: str
    dia_corto: str
    simulacros_creados: int
    simulacros_finalizados: int


class DistribucionArea(BaseModel):
    """Distribución de simulacros por área"""
    area: str
    codigo: str
    cantidad: int
    porcentaje: float
    color: str


class InstitucionReciente(BaseModel):
    """Institución registrada recientemente"""
    id: int
    nombre: str
    ciudad: Optional[str]
    fecha: str


class SimulacroReciente(BaseModel):
    """Simulacro creado recientemente"""
    id: int
    titulo: str
    area: str
    institucion_nombre: str
    estado: str
    fecha: str
    created_by_nombre: Optional[str] = None  # Nombre del creador
    created_by_tipo: Optional[str] = None    # "plataforma" o "institucion"


class SuperAdminDashboardStats(BaseModel):
    """Response completo del dashboard SuperAdmin"""
    kpis: List[KPICard]
    produccion_semanal: List[ProduccionSemanal]
    distribucion_areas: List[DistribucionArea]
    instituciones_recientes: List[InstitucionReciente]
    simulacros_recientes: List[SimulacroReciente]


# ==========================================
# HELPERS
# ==========================================

AREA_COLORS = {
    "Matemáticas": "#8b5cf6",
    "MATEMATICAS": "#8b5cf6",
    "Lectura Crítica": "#3b82f6",
    "LECTURA_CRITICA": "#3b82f6",
    "Ciencias Naturales": "#10b981",
    "CIENCIAS_NATURALES": "#10b981",
    "Ciencias Sociales": "#f59e0b",
    "Sociales y Ciudadanas": "#f59e0b",
    "SOCIALES_CIUDADANAS": "#f59e0b",
    "Inglés": "#ef4444",
    "INGLES": "#ef4444",
}

AREA_CODIGOS = {
    "Matemáticas": "MAT",
    "MATEMATICAS": "MAT",
    "Lectura Crítica": "LC",
    "LECTURA_CRITICA": "LC",
    "Ciencias Naturales": "CN",
    "CIENCIAS_NATURALES": "CN",
    "Ciencias Sociales": "CS",
    "Sociales y Ciudadanas": "CS",
    "SOCIALES_CIUDADANAS": "CS",
    "Inglés": "ING",
    "INGLES": "ING",
}


def format_date_short(dt: datetime) -> str:
    """Formatea fecha a formato corto (Ene 28)"""
    meses = {
        1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr", 5: "May", 6: "Jun",
        7: "Jul", 8: "Ago", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic"
    }
    return f"{meses[dt.month]} {dt.day}"


def get_dia_nombre(dt: datetime) -> tuple:
    """Retorna nombre del día y abreviatura"""
    dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    dias_cortos = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
    idx = dt.weekday()
    return dias[idx], dias_cortos[idx]


# ==========================================
# ENDPOINTS
# ==========================================

@router.get("/superadmin/stats", response_model=SuperAdminDashboardStats)
def get_superadmin_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Obtiene todas las métricas del dashboard de SuperAdmin.
    
    Incluye:
    - KPIs (instituciones, simulacros, estudiantes)
    - Ritmo de producción semanal
    - Distribución de contenido por área
    - Listados recientes (instituciones y simulacros)
    """
    # Validar permisos
    if not current_user.rol or current_user.rol.nombre != "admin":
        raise HTTPException(
            status_code=403, 
            detail="Solo el Super Admin puede acceder a este dashboard"
        )
    
    now = datetime.now()
    inicio_mes = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    inicio_semana = now - timedelta(days=6)  # Últimos 7 días
    
    # ==========================================
    # 1. KPIs
    # ==========================================
    
    # Total instituciones (excluyendo "Plataforma Maestra")
    total_instituciones = db.query(func.count(Institucion.id)).filter(
        Institucion.nit != "900000000-1"
    ).scalar() or 0
    
    nuevas_mes = db.query(func.count(Institucion.id)).filter(
        Institucion.created_at >= inicio_mes,
        Institucion.nit != "900000000-1"
    ).scalar() or 0
    
    # Total simulacros generados
    total_simulacros = db.query(func.count(Simulacro.id)).scalar() or 0
    
    simulacros_mes = db.query(func.count(Simulacro.id)).filter(
        Simulacro.created_at >= inicio_mes
    ).scalar() or 0
    
    # Total estudiantes alcanzados (usuarios con rol estudiante que han presentado al menos 1 simulacro)
    rol_estudiante = db.query(Rol).filter(Rol.nombre == "estudiante").first()
    estudiantes_activos = 0
    if rol_estudiante:
        # Estudiantes que han presentado al menos un simulacro
        estudiantes_activos = db.query(func.count(func.distinct(RespuestaEstudiante.usuario_id)))\
            .filter(RespuestaEstudiante.anulado.is_(False))\
            .scalar() or 0
    
    kpis = [
        KPICard(
            label="Total Instituciones",
            value=total_instituciones,
            change_value=f"+{nuevas_mes}" if nuevas_mes > 0 else None,
            change_type="new" if nuevas_mes > 0 else "neutral",
            change_label="este mes"
        ),
        KPICard(
            label="Simulacros Generados",
            value=total_simulacros,
            change_value=f"+{simulacros_mes}" if simulacros_mes > 0 else None,
            change_type="up" if simulacros_mes > 0 else "neutral",
            change_label="este mes"
        ),
        KPICard(
            label="Estudiantes Alcanzados",
            value=estudiantes_activos,
            change_value=None,
            change_type="neutral",
            change_label="con simulacros"
        ),
    ]
    
    # ==========================================
    # 2. Producción Semanal (últimos 7 días)
    # ==========================================
    
    produccion_semanal = []
    for i in range(6, -1, -1):  # De hace 6 días hasta hoy
        dia = now - timedelta(days=i)
        dia_inicio = dia.replace(hour=0, minute=0, second=0, microsecond=0)
        dia_fin = dia.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        # Simulacros creados ese día
        creados = db.query(func.count(Simulacro.id)).filter(
            Simulacro.created_at >= dia_inicio,
            Simulacro.created_at <= dia_fin
        ).scalar() or 0
        
        # Simulacros finalizados ese día (respuestas enviadas)
        finalizados = db.query(func.count(RespuestaEstudiante.id)).filter(
            RespuestaEstudiante.fecha_finalizacion >= dia_inicio,
            RespuestaEstudiante.fecha_finalizacion <= dia_fin
        ).filter(RespuestaEstudiante.anulado.is_(False)).scalar() or 0
        
        dia_nombre, dia_corto = get_dia_nombre(dia)
        
        produccion_semanal.append(ProduccionSemanal(
            dia=dia_nombre,
            dia_corto=dia_corto,
            simulacros_creados=creados,
            simulacros_finalizados=finalizados
        ))
    
    # ==========================================
    # 3. Distribución por Área
    # ==========================================
    
    areas_count = db.query(
        Simulacro.area,
        func.count(Simulacro.id).label("cantidad")
    ).group_by(Simulacro.area).all()
    
    total_areas = sum([a.cantidad for a in areas_count]) or 1  # Evitar división por 0
    
    distribucion_areas = []
    for area_row in areas_count:
        area_nombre = area_row.area
        cantidad = area_row.cantidad
        porcentaje = round((cantidad / total_areas) * 100, 1)
        
        distribucion_areas.append(DistribucionArea(
            area=area_nombre,
            codigo=AREA_CODIGOS.get(area_nombre, area_nombre[:3].upper()),
            cantidad=cantidad,
            porcentaje=porcentaje,
            color=AREA_COLORS.get(area_nombre, "#6b7280")
        ))
    
    # Ordenar por cantidad descendente
    distribucion_areas.sort(key=lambda x: x.cantidad, reverse=True)
    
    # ==========================================
    # 4. Instituciones Recientes
    # ==========================================
    
    instituciones_recientes_db = db.query(Institucion).filter(
        Institucion.nit != "900000000-1"
    ).order_by(Institucion.created_at.desc()).limit(5).all()
    
    instituciones_recientes = [
        InstitucionReciente(
            id=inst.id,
            nombre=inst.nombre,
            ciudad=inst.ciudad,
            fecha=format_date_short(inst.created_at) if inst.created_at else "N/A"
        )
        for inst in instituciones_recientes_db
    ]
    
    # ==========================================
    # 5. Simulacros Recientes
    # ==========================================
    
    simulacros_recientes_db = db.query(Simulacro).join(
        Institucion, Simulacro.institucion_id == Institucion.id
    ).order_by(Simulacro.created_at.desc()).limit(5).all()
    
    # Obtener info de creadores
    creator_ids = [sim.created_by for sim in simulacros_recientes_db if sim.created_by]
    creators = {}
    if creator_ids:
        creators_db = db.query(Usuario).filter(Usuario.id.in_(creator_ids)).all()
        for u in creators_db:
            rol_nombre = u.rol.nombre if u.rol else "desconocido"
            creators[u.id] = {
                "nombre": u.nombre,
                "tipo": "plataforma" if rol_nombre == "admin" else "institucion"
            }
    
    simulacros_recientes = []
    for sim in simulacros_recientes_db:
        creator_info = creators.get(sim.created_by, {})
        simulacros_recientes.append(SimulacroReciente(
            id=sim.id,
            titulo=sim.titulo,
            area=sim.area,
            institucion_nombre=sim.institucion.nombre if sim.institucion else "Sin institución",
            estado=sim.estado,
            fecha=format_date_short(sim.created_at) if sim.created_at else "N/A",
            created_by_nombre=creator_info.get("nombre"),
            created_by_tipo=creator_info.get("tipo")
        ))
    
    return SuperAdminDashboardStats(
        kpis=kpis,
        produccion_semanal=produccion_semanal,
        distribucion_areas=distribucion_areas,
        instituciones_recientes=instituciones_recientes,
        simulacros_recientes=simulacros_recientes
    )


# ==========================================
# DASHBOARD ADMIN INSTITUCIONAL (360°)
# ==========================================

class KPIInstitucional(BaseModel):
    """KPI para dashboard institucional"""
    label: str
    value: str
    subtitle: Optional[str] = None
    change_value: Optional[str] = None
    change_type: str = "neutral"
    progress: Optional[float] = None  # 0-100 para barra de progreso
    icon: str = "analytics"
    color: str = "blue"


class HeatmapCell(BaseModel):
    """Celda del heatmap áreas vs grupos"""
    area: str
    grupo: str
    grupo_id: int
    promedio: float
    total_estudiantes: int
    nivel: str  # "alto", "medio", "bajo", "critico"
    color: str


class DistribucionNivel(BaseModel):
    """Distribución de estudiantes por nivel de desempeño"""
    nivel: str
    rango: str
    cantidad: int
    porcentaje: float
    color: str


class DistribucionNivelPorArea(BaseModel):
    """Distribución de niveles para un área específica"""
    area: str
    area_codigo: str
    area_color: str
    total_evaluados: int
    niveles: List[DistribucionNivel]


class GrupoRendimiento(BaseModel):
    """Rendimiento de un grupo"""
    id: int
    nombre: str
    total_estudiantes: int
    promedio: float
    nivel: str
    color: str


class EstudianteTop(BaseModel):
    """Estudiante destacado"""
    id: int
    nombre: str
    grupo_nombre: Optional[str]
    puntaje: float
    posicion: int
    progreso: Optional[float] = None  # Cambio vs simulacro anterior


class CompetenciaDebil(BaseModel):
    """Competencia a fortalecer"""
    nombre: str
    area: str
    porcentaje_acierto: float
    nivel: str  # "critico", "bajo", "medio"


class AdminInstitucionDashboardStats(BaseModel):
    """Response completo del dashboard Admin Institucional"""
    kpis: List[KPIInstitucional]
    heatmap_grupos: List[HeatmapCell]
    distribucion_por_area: List[DistribucionNivelPorArea]  # Cambiado a por área
    rendimiento_grupos: List[GrupoRendimiento]
    top_estudiantes: List[EstudianteTop]
    top_progreso: List[EstudianteTop]
    competencias_debiles: List[CompetenciaDebil]
    tasa_finalizacion: float


def get_nivel_from_promedio(promedio: float) -> tuple:
    """Retorna nivel y color según el promedio"""
    if promedio >= 80:
        return "alto", "#10b981"  # emerald
    elif promedio >= 60:
        return "medio", "#6366f1"  # indigo
    elif promedio >= 40:
        return "bajo", "#f59e0b"  # amber
    else:
        return "critico", "#ef4444"  # red


@router.get("/institucion/stats", response_model=AdminInstitucionDashboardStats)
def get_admin_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Dashboard de Inteligencia Académica 360° para Admin Institucional.
    
    Incluye:
    - KPIs institucionales
    - Evolución de puntajes
    - Heatmap de desempeño (áreas vs grupos)
    - Distribución poblacional por niveles
    - Rankings (top estudiantes y top progreso)
    - Competencias a fortalecer
    """
    from app.models.grupo import Grupo
    
    # Validar permisos - Admin institucional o superior
    allowed_roles = ["admin", "docente"]
    if not current_user.rol or current_user.rol.nombre not in allowed_roles:
        raise HTTPException(
            status_code=403, 
            detail="No tiene permisos para acceder a este dashboard"
        )
    
    # Obtener institución del usuario
    institucion_id = current_user.institucion_id
    sede_id = current_user.sede_id if current_user.rol.nombre == 'docente' else None
    if not institucion_id:
        raise HTTPException(
            status_code=400,
            detail="Usuario no tiene institución asignada"
        )
    
    # ==========================================
    # 1. KPIs INSTITUCIONALES
    # ==========================================
    
    # Estudiantes evaluados (con al menos 1 respuesta)
    estudiantes_evaluados_query = db.query(
        func.count(func.distinct(RespuestaEstudiante.usuario_id))
    ).filter(
        RespuestaEstudiante.institucion_id == institucion_id,
        RespuestaEstudiante.anulado.is_(False)
    )
    if sede_id:
        estudiantes_evaluados_query = estudiantes_evaluados_query.join(
            Usuario, Usuario.id == RespuestaEstudiante.usuario_id
        ).filter(Usuario.sede_id == sede_id)
    estudiantes_evaluados = estudiantes_evaluados_query.scalar() or 0
    
    # Total estudiantes de la institución
    rol_estudiante = db.query(Rol).filter(Rol.nombre == "estudiante").first()
    total_estudiantes = 0
    if rol_estudiante:
        total_est_query = db.query(func.count(Usuario.id)).filter(
            Usuario.institucion_id == institucion_id,
            Usuario.rol_id == rol_estudiante.id,
            Usuario.activo == True
        )
        if sede_id:
            total_est_query = total_est_query.filter(Usuario.sede_id == sede_id)
        total_estudiantes = total_est_query.scalar() or 0
    
    cobertura = round((estudiantes_evaluados / total_estudiantes * 100), 1) if total_estudiantes > 0 else 0
    
    # Promedio general institucional
    promedio_query = db.query(
        func.avg(RespuestaEstudiante.puntaje_total)
    ).filter(
        RespuestaEstudiante.institucion_id == institucion_id,
        RespuestaEstudiante.anulado.is_(False)
    )
    if sede_id:
        promedio_query = promedio_query.join(
            Usuario, Usuario.id == RespuestaEstudiante.usuario_id
        ).filter(Usuario.sede_id == sede_id)
    promedio_general = promedio_query.scalar() or 0
    promedio_general = round(float(promedio_general), 1)
    
    # Mejor y peor área
    areas_stats_query = db.query(
        Simulacro.area,
        func.avg(RespuestaEstudiante.puntaje_total).label("promedio")
    ).join(
        RespuestaEstudiante, RespuestaEstudiante.simulacro_id == Simulacro.id
    ).filter(
        RespuestaEstudiante.institucion_id == institucion_id,
        RespuestaEstudiante.anulado.is_(False)
    )
    if sede_id:
        areas_stats_query = areas_stats_query.join(
            Usuario, Usuario.id == RespuestaEstudiante.usuario_id
        ).filter(Usuario.sede_id == sede_id)
    areas_stats = areas_stats_query.group_by(Simulacro.area).all()
    
    mejor_area = {"nombre": "Sin datos", "promedio": 0}
    peor_area = {"nombre": "Sin datos", "promedio": 100}
    
    for area_stat in areas_stats:
        prom = float(area_stat.promedio or 0)
        if prom > mejor_area["promedio"]:
            mejor_area = {"nombre": area_stat.area, "promedio": round(prom, 1)}
        if prom < peor_area["promedio"] and prom > 0:
            peor_area = {"nombre": area_stat.area, "promedio": round(prom, 1)}
    
    kpis = [
        KPIInstitucional(
            label="Estudiantes evaluados",
            value=f"{estudiantes_evaluados}",
            subtitle=f"de {total_estudiantes} registrados",
            progress=cobertura,
            icon="groups",
            color="blue"
        ),
        KPIInstitucional(
            label="Promedio general",
            value=f"{promedio_general}%",
            subtitle="Institucional",
            icon="analytics",
            color="purple"
        ),
        KPIInstitucional(
            label="Mejor área",
            value=mejor_area["nombre"][:15],
            subtitle=f"{mejor_area['promedio']}% promedio",
            progress=mejor_area["promedio"],
            icon="emoji_events",
            color="emerald"
        ),
        KPIInstitucional(
            label="Área a reforzar",
            value=peor_area["nombre"][:15] if peor_area["nombre"] != "Sin datos" else "Sin datos",
            subtitle=f"{peor_area['promedio']}% promedio" if peor_area["nombre"] != "Sin datos" else "",
            progress=peor_area["promedio"] if peor_area["nombre"] != "Sin datos" else 0,
            icon="warning",
            color="amber"
        ),
    ]

    # ==========================================
    # 2. HEATMAP: ÁREAS vs GRUPOS
    # ==========================================
    
    heatmap_query = db.query(
        Simulacro.area,
        Grupo.id.label("grupo_id"),
        Grupo.nombre.label("grupo_nombre"),
        func.avg(RespuestaEstudiante.puntaje_total).label("promedio"),
        func.count(func.distinct(RespuestaEstudiante.usuario_id)).label("total")
    ).join(
        RespuestaEstudiante, RespuestaEstudiante.simulacro_id == Simulacro.id
    ).join(
        Usuario, Usuario.id == RespuestaEstudiante.usuario_id
    ).join(
        Grupo, Grupo.id == Usuario.grupo_id
    ).filter(
        RespuestaEstudiante.institucion_id == institucion_id,
        RespuestaEstudiante.anulado.is_(False)
    )
    if sede_id:
        heatmap_query = heatmap_query.filter(Usuario.sede_id == sede_id)
    heatmap_raw = heatmap_query.group_by(
        Simulacro.area, Grupo.id, Grupo.nombre
    ).all()
    
    heatmap_grupos = []
    for row in heatmap_raw:
        promedio = round(float(row.promedio or 0), 1)
        nivel, color = get_nivel_from_promedio(promedio)
        heatmap_grupos.append(HeatmapCell(
            area=row.area,
            grupo=row.grupo_nombre,
            grupo_id=row.grupo_id,
            promedio=promedio,
            total_estudiantes=row.total,
            nivel=nivel,
            color=color
        ))
    
    # ==========================================
    # 4. DISTRIBUCIÓN POBLACIONAL POR ÁREA (Niveles ICFES)
    # ==========================================
    
    # Obtener todas las áreas con sus puntajes
    areas_scores_query = db.query(
        Simulacro.area,
        RespuestaEstudiante.puntaje_total
    ).join(
        RespuestaEstudiante, RespuestaEstudiante.simulacro_id == Simulacro.id
    ).filter(
        RespuestaEstudiante.institucion_id == institucion_id,
        RespuestaEstudiante.puntaje_total != None,
        RespuestaEstudiante.anulado.is_(False)
    )
    if sede_id:
        areas_scores_query = areas_scores_query.join(
            Usuario, Usuario.id == RespuestaEstudiante.usuario_id
        ).filter(Usuario.sede_id == sede_id)
    areas_scores_raw = areas_scores_query.all()
    
    # Agrupar puntajes por área
    areas_scores = {}
    for row in areas_scores_raw:
        area = row.area
        score = float(row.puntaje_total or 0)
        if area not in areas_scores:
            areas_scores[area] = []
        areas_scores[area].append(score)
    
    # Calcular distribución para cada área usando rangos oficiales ICFES
    distribucion_por_area = []
    
    # Colores para cada nivel (orden: nivel 1/bajo a nivel 4/alto)
    NIVEL_COLORS = ["#ef4444", "#f59e0b", "#6366f1", "#10b981"]  # rojo, amber, indigo, verde
    
    for area_nombre, scores in areas_scores.items():
        # Obtener rangos oficiales para esta área
        area_canonical = AREA_CANONICAL.get(area_nombre, area_nombre)
        rangos = RANGOS_ICFES_POR_AREA.get(area_canonical, [
            (35, "Nivel 1"), (55, "Nivel 2"), (70, "Nivel 3"), (100, "Nivel 4")
        ])
        
        # Inicializar contadores por nivel
        niveles_count = {i: 0 for i in range(len(rangos))}
        
        # Clasificar cada puntaje
        for score in scores:
            _, nivel_idx = get_nivel_icfes(area_nombre, score)
            niveles_count[nivel_idx] += 1
        
        total = len(scores) or 1
        
        # Construir lista de niveles (ordenados de mayor a menor para el gráfico)
        niveles = []
        for idx in reversed(range(len(rangos))):
            limite, nombre = rangos[idx]
            limite_inferior = rangos[idx - 1][0] + 1 if idx > 0 else 0
            
            niveles.append(DistribucionNivel(
                nivel=nombre,
                rango=f"{limite_inferior}-{limite}",
                cantidad=niveles_count[idx],
                porcentaje=round(niveles_count[idx] / total * 100, 1),
                color=NIVEL_COLORS[idx]
            ))
        
        distribucion_por_area.append(DistribucionNivelPorArea(
            area=area_nombre,
            area_codigo=AREA_CODIGOS.get(area_nombre, area_nombre[:3].upper()),
            area_color=AREA_COLORS.get(area_nombre, "#6b7280"),
            total_evaluados=total,
            niveles=niveles
        ))
    
    # Ordenar por nombre de área
    distribucion_por_area.sort(key=lambda x: x.area)
    
    # ==========================================
    # 5. RENDIMIENTO POR GRUPO
    # ==========================================
    
    grupos_stats_query = db.query(
        Grupo.id,
        Grupo.nombre,
        func.count(func.distinct(RespuestaEstudiante.usuario_id)).label("total"),
        func.avg(RespuestaEstudiante.puntaje_total).label("promedio")
    ).join(
        Usuario, Usuario.grupo_id == Grupo.id
    ).join(
        RespuestaEstudiante, RespuestaEstudiante.usuario_id == Usuario.id
    ).filter(
        Grupo.institucion_id == institucion_id,
        RespuestaEstudiante.anulado.is_(False)
    )
    if sede_id:
        grupos_stats_query = grupos_stats_query.filter(Usuario.sede_id == sede_id)
    grupos_stats = grupos_stats_query.group_by(Grupo.id, Grupo.nombre).order_by(
        func.avg(RespuestaEstudiante.puntaje_total).desc()
    ).limit(10).all()
    
    rendimiento_grupos = []
    for row in grupos_stats:
        promedio = round(float(row.promedio or 0), 1)
        nivel, color = get_nivel_from_promedio(promedio)
        rendimiento_grupos.append(GrupoRendimiento(
            id=row.id,
            nombre=row.nombre,
            total_estudiantes=row.total,
            promedio=promedio,
            nivel=nivel,
            color=color
        ))
    
    # ==========================================
    # 6. TOP 5 ESTUDIANTES (Mejor puntaje)
    # ==========================================
    
    top_query = db.query(
        Usuario.id,
        Usuario.nombre,
        Grupo.nombre.label("grupo_nombre"),
        func.avg(RespuestaEstudiante.puntaje_total).label("promedio")
    ).join(
        RespuestaEstudiante, RespuestaEstudiante.usuario_id == Usuario.id
    ).outerjoin(
        Grupo, Grupo.id == Usuario.grupo_id
    ).filter(
        RespuestaEstudiante.institucion_id == institucion_id,
        RespuestaEstudiante.anulado.is_(False)
    )
    if sede_id:
        top_query = top_query.filter(Usuario.sede_id == sede_id)
    top_raw = top_query.group_by(
        Usuario.id, Usuario.nombre, Grupo.nombre
    ).order_by(
        func.avg(RespuestaEstudiante.puntaje_total).desc()
    ).limit(5).all()
    
    top_estudiantes = [
        EstudianteTop(
            id=row.id,
            nombre=row.nombre,
            grupo_nombre=row.grupo_nombre,
            puntaje=round(float(row.promedio or 0), 1),
            posicion=idx + 1
        )
        for idx, row in enumerate(top_raw)
    ]
    
    # Top Progreso (simplificado - por ahora igual que top, se puede mejorar)
    top_progreso = top_estudiantes[:5]  # TODO: Calcular progreso real entre simulacros
    
    # ==========================================
    # 7. COMPETENCIAS DÉBILES (desde respuestas_detalladas)
    # ==========================================
    
    # Esto requeriría parsear el JSONB de respuestas_detalladas
    # Por ahora devolvemos lista vacía para no mostrar datos falsos si no hay suficiente info
    competencias_debiles = []
    
    # TODO: Implementar lógica real parseando los JSONs de respuestas para calcular fallos por competencia
    # Placeholder comentado para referencia futura:
    # competencias_debiles = [
    #     CompetenciaDebil(
    #         nombre="Uso comprensivo del conocimiento científico",
    #         area="Ciencias Naturales",
    #         porcentaje_acierto=42.0,
    #         nivel="critico"
    #     ),
    # ...
    # ]
    
    # ==========================================
    # 8. TASA DE FINALIZACIÓN
    # ==========================================

    # Tasa de finalización (con puntaje vs iniciados)
    iniciados_query = db.query(func.count(RespuestaEstudiante.id)).filter(
        RespuestaEstudiante.institucion_id == institucion_id,
        RespuestaEstudiante.anulado.is_(False)
    )
    finalizados_query = db.query(func.count(RespuestaEstudiante.id)).filter(
        RespuestaEstudiante.institucion_id == institucion_id,
        RespuestaEstudiante.puntaje_total != None,
        RespuestaEstudiante.anulado.is_(False)
    )
    if sede_id:
        iniciados_query = iniciados_query.join(
            Usuario, Usuario.id == RespuestaEstudiante.usuario_id
        ).filter(Usuario.sede_id == sede_id)
        finalizados_query = finalizados_query.join(
            Usuario, Usuario.id == RespuestaEstudiante.usuario_id
        ).filter(Usuario.sede_id == sede_id)
    iniciados = iniciados_query.scalar() or 0
    finalizados = finalizados_query.scalar() or 0
    
    tasa_finalizacion = round((finalizados / iniciados * 100), 1) if iniciados > 0 else 0
    
    return AdminInstitucionDashboardStats(
        kpis=kpis,
        heatmap_grupos=heatmap_grupos,
        distribucion_por_area=distribucion_por_area,
        rendimiento_grupos=rendimiento_grupos,
        top_estudiantes=top_estudiantes,
        top_progreso=top_progreso,
        competencias_debiles=competencias_debiles,
        tasa_finalizacion=tasa_finalizacion
    )
