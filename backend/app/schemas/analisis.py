from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


NodeType = Literal["group", "student", "area", "competencia"]
TrendState = Literal["subiendo", "bajando", "estable"]


class CanvasNodeDTO(BaseModel):
    id: str
    type: NodeType
    label: str
    meta: Dict[str, Any] = Field(default_factory=dict)


class AreaMetricasTendencia(BaseModel):
    estado: TrendState
    pendiente: float
    umbral_estable: float = 1.0
    delta_primer_ultimo: float = 0.0
    confiabilidad_baja: bool = False


class SeriePuntajeItem(BaseModel):
    respuesta_id: int
    fecha: datetime
    puntaje_total: float
    simulacro_titulo: str


class SerieCompetenciaPunto(BaseModel):
    fecha: datetime
    valor: float
    respuesta_id: int


class SerieCompetenciaItem(BaseModel):
    competencia: str
    puntos: List[SerieCompetenciaPunto]


class ResumenCompetenciaItem(BaseModel):
    competencia: str
    promedio: float
    ultimo: float
    variacion: float


class EntityRef(BaseModel):
    id: int
    nombre: str


class AreaRef(BaseModel):
    codigo: str
    nombre: str


class AreaMetricasResponse(BaseModel):
    estudiante: EntityRef
    grupo: EntityRef
    area: AreaRef
    tendencia: AreaMetricasTendencia
    serie_puntaje: List[SeriePuntajeItem]
    series_competencia: List[SerieCompetenciaItem]
    resumen_competencias: List[ResumenCompetenciaItem]
    competencia_enfoque: Optional[str] = None
