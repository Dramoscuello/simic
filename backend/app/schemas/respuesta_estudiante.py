from pydantic import BaseModel
from typing import Dict, Optional, Any
from datetime import datetime

class RespuestaEstudianteBase(BaseModel):
    respuestas: Dict[str, str]
    tiempo_empleado: Optional[int] = 0

class RespuestaEstudianteCreate(RespuestaEstudianteBase):
    pass

class RespuestaEstudianteResponse(RespuestaEstudianteBase):
    id: int
    simulacro_id: int
    usuario_id: int
    institucion_id: int
    total_correctas: int
    total_incorrectas: int
    puntaje_total: Optional[float] = None
    fecha_inicio: Optional[datetime] = None
    fecha_finalizacion: Optional[datetime] = None
    created_at: Optional[datetime] = None
    analisis_ia: Optional[Dict[str, Any]] = None
    fraude: bool = False # Nuevo campo expuesto
    informe_generado: bool = False
    informe_url: Optional[str] = None
    anulado: bool = False
    reset_at: Optional[datetime] = None
    reset_by: Optional[int] = None
    reset_reason: Optional[str] = None
    
    class Config:
        from_attributes = True

# Nuevos esquemas para el flujo seguro
class RespuestaEstudianteStart(BaseModel):
    """Schema para iniciar un intento"""
    pass

class RespuestaEstudianteUpdate(BaseModel):
    """Schema para guardar progreso parcial"""
    respuestas_parciales: Dict[str, str]
    tiempo_empleado: Optional[int] = 0

class RespuestaEstudianteFinalize(BaseModel):
    """Schema para finalizar el intento"""
    respuestas: Dict[str, str]
    tiempo_empleado: Optional[int] = 0
