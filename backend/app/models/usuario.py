from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.config import Base

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=True) # Estudiantes podrian no tener email
    hashed_password = Column(String(255), nullable=False)
    
    tipo_documento = Column(String(10), nullable=False) # TI, CC, CE
    numero_documento = Column(String(20), unique=True, nullable=False, index=True)
    
    institucion_id = Column(Integer, ForeignKey("instituciones.id"))
    rol_id = Column(Integer, ForeignKey("roles.id"))
    grupo_id = Column(Integer, ForeignKey("grupos.id"), nullable=True)
    sede_id = Column(Integer, ForeignKey("sedes.id"), nullable=True)

    activo = Column(Boolean, default=True)
    ultimo_acceso = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relaciones
    institucion = relationship("Institucion", backref="usuarios")
    rol = relationship("Rol", backref="usuarios")
    grupo = relationship("Grupo", backref="estudiantes")
    sede = relationship("Sede", backref="usuarios")
