from sqlalchemy import Column, Integer, String, Text, Boolean, Date, ForeignKey, DateTime, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB
from app.database.config import Base


class Simulacro(Base):
    __tablename__ = "simulacros"

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String(255), nullable=False)
    descripcion = Column(Text, nullable=True)
    
    # Área del simulacro (sin GLOBAL)
    area = Column(String(50), CheckConstraint("area IN ('MATEMATICAS', 'LECTURA_CRITICA', 'CIENCIAS_NATURALES', 'SOCIALES_CIUDADANAS', 'INGLES', 'Matemáticas', 'Lectura Crítica', 'Ciencias Naturales', 'Ciencias Sociales', 'Inglés')"), nullable=False)
    
    version = Column(String(50), nullable=True)  # v1, v2025-01
    
    # Campo estrella: Almacena todo el output de Claude
    contenido = Column(JSONB, nullable=False)
    
    total_preguntas = Column(Integer, default=30)
    duracion_minutos = Column(Integer, nullable=True)
    
    institucion_id = Column(Integer, ForeignKey("instituciones.id"))
    sede_id = Column(Integer, ForeignKey("sedes.id"), nullable=True)

    # Auditoría: Usuario que creó el simulacro (sin FK estricta para evitar problemas si se elimina el usuario)
    created_by = Column(Integer, nullable=True)  # ID del usuario creador

    # Estado del simulacro: 'activo', 'finalizado'
    # - activo: Disponible para que estudiantes lo presenten (si activo=True)
    # - finalizado: Todos los estudiantes hicieron el simulacro o expiró
    # Nota: 'borrador' fue eliminado. Ahora usamos activo=False para ocultar simulacros.
    estado = Column(
        String(20), 
        CheckConstraint("estado IN ('activo', 'finalizado')"),
        default='activo',
        nullable=False
    )
    
    # Visibilidad del simulacro (solo modificable por SuperAdmin)
    # - activo=False: Solo SuperAdmin puede ver el simulacro (modo edición/revisión)
    # - activo=True: Visible para todos los usuarios según sus permisos
    activo = Column(Boolean, default=False)
    
    fecha_disponible_desde = Column(Date, nullable=True)
    fecha_disponible_hasta = Column(Date, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relaciones
    institucion = relationship("Institucion", backref="simulacros")
    sede = relationship("Sede", backref="simulacros")

