from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class InstitucionBase(BaseModel):
    nombre: str
    codigo_dane: str
    nit: Optional[str] = None
    direccion: Optional[str] = None
    telefono: Optional[str] = None
    email_contacto: EmailStr
    ciudad: Optional[str] = None
    departamento: Optional[str] = None
    activo: bool = True
    # Datos del rector
    nombre_rector: str
    email_rector: EmailStr
    telefono_rector: Optional[str] = None

class InstitucionCreate(InstitucionBase):
    pass

class InstitucionUpdate(BaseModel):
    nombre: Optional[str] = None
    nit: Optional[str] = None
    direccion: Optional[str] = None
    telefono: Optional[str] = None
    email_contacto: Optional[EmailStr] = None
    ciudad: Optional[str] = None
    departamento: Optional[str] = None
    activo: Optional[bool] = None
    nombre_rector: Optional[str] = None
    email_rector: Optional[EmailStr] = None
    telefono_rector: Optional[str] = None

class Institucion(InstitucionBase):
    id: int
    fecha_registro: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
