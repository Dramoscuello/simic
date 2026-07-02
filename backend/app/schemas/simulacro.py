from pydantic import BaseModel
from typing import Optional, Dict, Any, Literal
from datetime import date, datetime


class SimulacroBase(BaseModel):
    titulo: str
    descripcion: Optional[str] = None
    area: str
    version: Optional[str] = None
    contenido: Dict[str, Any]  # El JSON completo de preguntas
    total_preguntas: int = 30
    duracion_minutos: Optional[int] = None
    institucion_id: int
    sede_id: Optional[int] = None
    estado: Literal['activo', 'finalizado'] = 'activo'
    activo: bool = False  # Default False para que solo SuperAdmin vea el simulacro inicialmente
    fecha_disponible_desde: Optional[date] = None
    fecha_disponible_hasta: Optional[date] = None


class SimulacroCreate(SimulacroBase):
    pass


class SimulacroUpdate(BaseModel):
    titulo: Optional[str] = None
    descripcion: Optional[str] = None
    area: Optional[str] = None
    version: Optional[str] = None
    contenido: Optional[Dict[str, Any]] = None
    total_preguntas: Optional[int] = None
    duracion_minutos: Optional[int] = None
    institucion_id: Optional[int] = None
    sede_id: Optional[int] = None
    estado: Optional[Literal['activo', 'finalizado']] = None
    activo: Optional[bool] = None
    fecha_disponible_desde: Optional[date] = None
    fecha_disponible_hasta: Optional[date] = None


class SimulacroResetRequest(BaseModel):
    motivo: Optional[str] = None


class Simulacro(SimulacroBase):
    id: int
    created_by: Optional[int] = None  # ID del usuario creador
    created_by_nombre: Optional[str] = None  # Nombre del creador
    created_by_tipo: Optional[str] = None    # "superadmin" o nombre de institución
    institucion_nombre: Optional[str] = None  # Nombre de la institución
    sede_nombre: Optional[str] = None  # Nombre de la sede
    mi_intento_activo: Optional[bool] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
