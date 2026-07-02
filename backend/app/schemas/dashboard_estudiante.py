from pydantic import BaseModel
from typing import List, Optional

class AreaPerformance(BaseModel):
    area: str
    puntaje: float
    total_intentos: int
    estado: str  # "ok", "warning", "insufficient_data"

class StudentDashboardStats(BaseModel):
    global_score: float
    simulacros_completados: int
    areas_performance: List[AreaPerformance]
    ranking_percentil: Optional[float] = None  # Opcional: top X% del curso

class StudentDashboardResponse(BaseModel):
    stats: StudentDashboardStats
