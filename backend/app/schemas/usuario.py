from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from app.schemas.institucion import Institucion
from app.schemas.rol import Rol
from app.schemas.grupo import Grupo
from app.schemas.sede import Sede

class UsuarioBase(BaseModel):
    nombre: str
    email: Optional[EmailStr] = None
    tipo_documento: str
    numero_documento: str
    institucion_id: int
    rol_id: int
    grupo_id: Optional[int] = None
    sede_id: Optional[int] = None
    activo: bool = True

class UsuarioCreate(UsuarioBase):
    password: str

class UsuarioUpdate(BaseModel):
    nombre: Optional[str] = None
    email: Optional[EmailStr] = None
    tipo_documento: Optional[str] = None
    numero_documento: Optional[str] = None
    institucion_id: Optional[int] = None
    rol_id: Optional[int] = None
    grupo_id: Optional[int] = None
    sede_id: Optional[int] = None
    activo: Optional[bool] = None
    password: Optional[str] = None # Opcional para cambio de clave

class Usuario(UsuarioBase):
    id: int
    ultimo_acceso: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    # Nested objects para respuestas completas (opcional)
    institucion: Optional[Institucion] = None 
    rol: Optional[Rol] = None
    grupo: Optional[Grupo] = None
    sede: Optional[Sede] = None

    class Config:
        from_attributes = True
