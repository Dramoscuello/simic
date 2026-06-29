from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict
from app.database.config import get_db
from app.api.deps import get_current_active_user
from app.models.usuario import Usuario
from app.models.respuesta_estudiante import RespuestaEstudiante
from app.models.simulacro import Simulacro
from app.schemas.dashboard_estudiante import StudentDashboardResponse, StudentDashboardStats, AreaPerformance

router = APIRouter(
    prefix="/estudiantes",
    tags=["estudiantes"]
)

@router.get("/dashboard-stats", response_model=StudentDashboardResponse)
def get_student_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_user)
):
    """
    Retorna estadisticas consolidadas para el dashboard del estudiante.
    - Promedio global
    - Desempeño por area
    """
    if current_user.rol.nombre != 'estudiante':
        # Permitir a otros roles verlo si quisieran simular, pero idealmente es para estudiantes
        pass

    # 1. Calcular promedio global
    # Promedio de todos los simulacros finalizados
    avg_query = db.query(func.avg(RespuestaEstudiante.puntaje_total))        .filter(RespuestaEstudiante.usuario_id == current_user.id)        .filter(RespuestaEstudiante.puntaje_total != None)        .filter(RespuestaEstudiante.anulado.is_(False))
    
    global_average = avg_query.scalar() or 0.0
    
    # Total completados
    total_finished = db.query(RespuestaEstudiante)        .filter(RespuestaEstudiante.usuario_id == current_user.id)        .filter(RespuestaEstudiante.puntaje_total != None)        .filter(RespuestaEstudiante.anulado.is_(False))        .count()

    # 2. Calcular desempeño por áreas
    # Group by Simulacro.area
    areas_query = db.query(
        Simulacro.area,
        func.avg(RespuestaEstudiante.puntaje_total).label('avg_score'),
        func.count(RespuestaEstudiante.id).label('count')
    ).join(RespuestaEstudiante)     .filter(RespuestaEstudiante.usuario_id == current_user.id)     .filter(RespuestaEstudiante.puntaje_total != None)     .filter(RespuestaEstudiante.anulado.is_(False))     .group_by(Simulacro.area)     .all()
    
    # Crear mapa de resultados
    area_map = {row.area: {"score": float(row.avg_score), "count": row.count} for row in areas_query}
    
    # Lista fija de areas para asegurar que siempre devolvemos estructura completa (aunque sea vacia)
    all_areas = ["MATEMATICAS", "INGLES", "LECTURA_CRITICA", "CIENCIAS_NATURALES", "SOCIALES_CIUDADANAS"]
    
    performance_list = []
    
    for area_code in all_areas:
        data = area_map.get(area_code)
        
        if data:
            score = data["score"]
            count = data["count"]
            # Determinar estado
            if count < 1: 
                estado = "insufficient_data"
            elif score < 60:
                estado = "warning" # Rojo/Naranja
            else:
                estado = "ok" # Verde
        else:
            score = 0.0
            count = 0
            estado = "insufficient_data"
            
        performance_list.append(AreaPerformance(
            area=area_code,
            puntaje=round(score, 1),
            total_intentos=count,
            estado=estado
        ))
        
    stats = StudentDashboardStats(
        global_score=round(float(global_average), 1),
        simulacros_completados=total_finished,
        areas_performance=performance_list
    )
    
    return StudentDashboardResponse(stats=stats)
