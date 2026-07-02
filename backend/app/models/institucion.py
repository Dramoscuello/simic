from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.config import Base


class Institucion(Base):
    __tablename__ = "instituciones"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(255), nullable=False)
    codigo_dane = Column(String(12), unique=True, nullable=False, index=True)
    nit = Column(String(20), unique=True, index=True)
    direccion = Column(String(255))
    telefono = Column(String(20))
    email_contacto = Column(String(255), nullable=False)
    ciudad = Column(String(100))
    departamento = Column(String(100))
    activo = Column(Boolean, default=True)

    # Datos del rector
    nombre_rector = Column(String(255), nullable=False)
    email_rector = Column(String(255), nullable=False)
    telefono_rector = Column(String(20))

    fecha_registro = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
