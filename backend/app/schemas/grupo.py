from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.schemas.sede import Sede

class GrupoBase(BaseModel):
    nombre: str
    institucion_id: int
    sede_id: Optional[int] = None

class GrupoCreate(BaseModel):
    nombre: str
    institucion_id: Optional[int] = None
    sede_id: Optional[int] = None

class GrupoUpdate(BaseModel):
    nombre: Optional[str] = None
    sede_id: Optional[int] = None
    
class Grupo(GrupoBase):
    id: int
    estudiantes_count: Optional[int] = 0
    sede: Optional[Sede] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
