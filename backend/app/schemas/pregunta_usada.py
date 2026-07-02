from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class PreguntaUsadaBase(BaseModel):
    """Schema base para preguntas usadas"""
    institucion_id: int
    area: str
    pregunta: str
    tema: Optional[str] = None
    componente: Optional[str] = None
    competencia: Optional[str] = None
    version_simulacro: Optional[str] = None
    simulacro_id: Optional[int] = None


class PreguntaUsadaCreate(PreguntaUsadaBase):
    """Schema para crear una pregunta usada individualmente"""
    pass


class PreguntaUsadaBulkCreate(BaseModel):
    """Schema para crear múltiples preguntas usadas desde un simulacro"""
    simulacro_id: int
    version_simulacro: Optional[str] = None


class PreguntaUsadaUpdate(BaseModel):
    """Schema para actualizar una pregunta usada"""
    tema: Optional[str] = None
    componente: Optional[str] = None
    competencia: Optional[str] = None
    version_simulacro: Optional[str] = None


class PreguntaUsada(PreguntaUsadaBase):
    """Schema para respuesta con todos los campos"""
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class PreguntaUsadaExport(BaseModel):
    """Schema simplificado para exportación TXT"""
    pregunta: str
    tema: Optional[str] = None
    componente: Optional[str] = None
    competencia: Optional[str] = None


class PreguntaUsadaStats(BaseModel):
    """Estadísticas de preguntas usadas por institución"""
    institucion_id: int
    total_preguntas: int
    por_area: dict  # {"Matemáticas": 30, "Lectura Crítica": 25, ...}
