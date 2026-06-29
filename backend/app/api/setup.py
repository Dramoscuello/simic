import re
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user
from app.core.security import get_password_hash
from app.database.config import get_db
from app.models.institucion import Institucion
from app.models.rol import Rol
from app.models.sede import Sede
from app.models.usuario import Usuario

router = APIRouter(prefix="/setup", tags=["setup"])


class AdminSetup(BaseModel):
    es_rector: bool = False
    cargo: Optional[str] = Field(None, max_length=100)
    nombres: Optional[str] = Field(None, max_length=255)
    apellidos: Optional[str] = Field(None, max_length=255)
    email: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=8, max_length=255)
    password_confirm: str = Field(..., min_length=8, max_length=255)


class InstitucionSetup(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=255)
    codigo_dane: str = Field(..., min_length=12, max_length=12)
    nit: str = Field(..., min_length=1, max_length=20)
    direccion: str = Field(..., min_length=1, max_length=255)
    telefono: Optional[str] = Field(None, max_length=20)
    email_contacto: str = Field(..., min_length=1, max_length=255)
    nombre_rector: str = Field(..., min_length=1, max_length=255)
    email_rector: str = Field(..., min_length=1, max_length=255)
    telefono_rector: Optional[str] = Field(None, max_length=20)

    @field_validator("codigo_dane")
    def validar_dane(cls, v):
        if not re.fullmatch(r"\d{12}", v):
            raise ValueError("El código DANE debe tener exactamente 12 dígitos numéricos")
        return v


class SetupPayload(BaseModel):
    institucion: InstitucionSetup
    admin: AdminSetup

    @field_validator("admin")
    def validar_admin(cls, v):
        if v.password != v.password_confirm:
            raise ValueError("Las contraseñas no coinciden")
        if not v.es_rector and (not v.nombres or not v.apellidos):
            raise ValueError("Debe ingresar nombres y apellidos del administrador")
        return v


@router.get("/status")
def setup_status(db: Session = Depends(get_db)):
    """Indica si la aplicación necesita configuración inicial."""
    necesita = db.query(Institucion).first() is None
    return {"needs_setup": necesita}


@router.post("/")
def create_setup(payload: SetupPayload, db: Session = Depends(get_db)):
    """Crea la institución, el administrador y los modelos de IA iniciales."""
    if db.query(Institucion).first() is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="La aplicación ya fue configurada",
        )

    # Crear institución
    institucion = Institucion(
        nombre=payload.institucion.nombre,
        codigo_dane=payload.institucion.codigo_dane,
        nit=payload.institucion.nit,
        direccion=payload.institucion.direccion,
        telefono=payload.institucion.telefono,
        email_contacto=payload.institucion.email_contacto,
        nombre_rector=payload.institucion.nombre_rector,
        email_rector=payload.institucion.email_rector,
        telefono_rector=payload.institucion.telefono_rector,
    )
    db.add(institucion)
    db.commit()
    db.refresh(institucion)

    # Crear sede principal por defecto
    sede_principal = Sede(
        nombre="Sede Principal",
        direccion=institucion.direccion,
        telefono=institucion.telefono,
        activo=True,
        institucion_id=institucion.id,
    )
    db.add(sede_principal)
    db.commit()
    db.refresh(sede_principal)

    # Crear usuario administrador
    admin_rol = db.query(Rol).filter(Rol.nombre == "admin").first()
    if not admin_rol:
        admin_rol = Rol(nombre="admin", descripcion="Rol de administrador de la institución")
        db.add(admin_rol)
        db.commit()
        db.refresh(admin_rol)

    if payload.admin.es_rector:
        admin_nombre = payload.institucion.nombre_rector
    else:
        admin_nombre = f"{payload.admin.nombres} {payload.admin.apellidos}".strip()

    admin = Usuario(
        nombre=admin_nombre,
        email=payload.admin.email,
        hashed_password=get_password_hash(payload.admin.password),
        tipo_documento="CC",
        numero_documento=payload.institucion.codigo_dane,
        institucion_id=institucion.id,
        rol_id=admin_rol.id,
        activo=True,
    )
    db.add(admin)
    db.commit()

    return {
        "message": "Configuración inicial completada",
        "institucion_id": institucion.id,
        "admin_email": admin.email,
    }


@router.get("/institucion/public")
def get_institucion_public(db: Session = Depends(get_db)):
    """Devuelve el nombre de la institución configurada (público, sin auth)."""
    institucion = db.query(Institucion).first()
    if not institucion:
        return {"nombre": None, "configured": False}
    return {"nombre": institucion.nombre, "configured": True}
