from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ReviewPreguntaBase(BaseModel):
    """Campos base para crear/actualizar una revisión"""
    simulacro_id: int
    pregunta_numero: int
    revision: str


class ReviewPreguntaCreate(ReviewPreguntaBase):
    """Schema para crear una nueva revisión"""
    pass


class ReviewPreguntaUpdate(BaseModel):
    """Schema para actualizar una revisión (parcial)"""
    revision: Optional[str] = None
    resuelto: Optional[bool] = None


class ReviewPreguntaResponse(ReviewPreguntaBase):
    """Schema de respuesta con todos los campos"""
    id: int
    usuario_id: Optional[int] = None
    resuelto: bool
    created_at: datetime
    updated_at: datetime
    
    # Campos adicionales para UI
    usuario_nombre: Optional[str] = None  # Se llena en el endpoint
    
    class Config:
        from_attributes = True


class ReviewPreguntaListResponse(BaseModel):
    """Response para listar revisiones de un simulacro"""
    total: int
    pendientes: int
    resueltas: int
    reviews: list[ReviewPreguntaResponse]
