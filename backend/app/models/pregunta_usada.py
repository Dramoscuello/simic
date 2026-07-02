from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from app.database.config import Base


class PreguntaUsada(Base):
    """
    Tracking de preguntas ya utilizadas por institución y área.
    Permite evitar repetición de preguntas en simulacros futuros.
    """
    __tablename__ = "preguntas_usadas"

    id = Column(Integer, primary_key=True, index=True)
    
    # Relaciones principales
    institucion_id = Column(Integer, ForeignKey("instituciones.id", ondelete="CASCADE"), nullable=False)
    
    # Área del simulacro (texto para flexibilidad, coincide con campo 'area' de simulacros)
    area = Column(String(100), nullable=False)
    
    # Texto completo de la pregunta (para comparación y exportación)
    pregunta = Column(Text, nullable=False)
    
    # Metadatos ICFES de la pregunta
    tema = Column(String(255), nullable=True)  # "Álgebra - Ecuaciones lineales", "Geometría - Áreas"
    componente = Column(String(255), nullable=True)  # Componente ICFES evaluado
    competencia = Column(String(255), nullable=True)  # Competencia ICFES evaluada
    
    # Versión del simulacro donde se usó (para tracking)
    version_simulacro = Column(String(50), nullable=True)  # "v2025-01", "v2026-01"
    
    # ID del simulacro origen (opcional, para trazabilidad)
    simulacro_id = Column(Integer, ForeignKey("simulacros.id", ondelete="SET NULL"), nullable=True)
    
    # Hash SHA-256 del contenido (contexto + enunciado) para detección rápida de duplicados
    hash_contenido = Column(String(64), nullable=True, index=True)

    # Embedding semántico para deduplicación conceptual (Gate 3C)
    embedding = Column(Vector(1536), nullable=True)
    embedding_model = Column(String(64), nullable=True)
    embedding_updated_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relaciones
    institucion = relationship("Institucion", backref="preguntas_usadas")
    simulacro = relationship("Simulacro", backref="preguntas_registradas")

    # Índices para consultas frecuentes
    __table_args__ = (
        Index('idx_preguntas_usadas_institucion', 'institucion_id'),
        Index('idx_preguntas_usadas_area', 'area'),
        Index('idx_preguntas_usadas_version', 'version_simulacro'),
        Index('idx_preguntas_usadas_institucion_area', 'institucion_id', 'area'),
    )
