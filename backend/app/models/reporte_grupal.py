from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, UniqueConstraint, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB
from app.database.config import Base

class ReporteGrupal(Base):
    """
    Almacena el reporte consolidado de un grupo de estudiantes para un simulacro especifico.
    Analiza tendencias, fortalezas y debilidades colectivas.
    """
    __tablename__ = "reportes_grupales"

    id = Column(Integer, primary_key=True, index=True)
    
    simulacro_id = Column(Integer, ForeignKey("simulacros.id"), nullable=False)
    institucion_id = Column(Integer, ForeignKey("instituciones.id"), nullable=False)
    
    # Contenido del informe generado por la IA
    informe_contenido = Column(Text, nullable=False)
    
    # Metadatos estadisticos (promedio grupal, temas criticos, desviacion, etc)
    estadisticas_agregadas = Column(JSONB, nullable=True) 
    anulado = Column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relaciones
    simulacro = relationship("Simulacro", backref="reportes_grupales")
    institucion = relationship("Institucion", backref="reportes_grupales")

    # Constraint: Un simulacro tiene un solo reporte grupal oficial (se puede actualizar)
    __table_args__ = (
        UniqueConstraint('simulacro_id', 'institucion_id', name='uq_reporte_grupal_simulacro'),
    )
