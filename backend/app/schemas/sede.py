from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class SedeBase(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=255)
    direccion: Optional[str] = None
    telefono: Optional[str] = None
    activo: bool = True


class SedeCreate(SedeBase):
    institucion_id: Optional[int] = None


class SedeUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=1, max_length=255)
    direccion: Optional[str] = None
    telefono: Optional[str] = None
    activo: Optional[bool] = None


class Sede(SedeBase):
    id: int
    institucion_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
