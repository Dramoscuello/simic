from sqlalchemy import Column, Integer, Text, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.config import Base


class ReviewPregunta(Base):
    """
    Tabla para almacenar notas de revisión sobre preguntas específicas.
    
    Como las preguntas están en JSONB dentro del simulacro, referenciamos
    por simulacro_id + pregunta_numero (el 'id' o 'numero' dentro del JSON).
    """
    __tablename__ = "review_preguntas"

    id = Column(Integer, primary_key=True, index=True)
    
    # Referencias a la pregunta (simulacro + número de pregunta dentro del JSON)
    simulacro_id = Column(Integer, ForeignKey("simulacros.id", ondelete="CASCADE"), nullable=False)
    pregunta_numero = Column(Integer, nullable=False)  # El 'id' o 'numero' de la pregunta en el JSON
    
    # Usuario que creó la revisión
    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
    
    # Contenido de la revisión
    revision = Column(Text, nullable=False)  # La nota/comentario
    
    # Estado de la revisión
    resuelto = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relaciones
    simulacro = relationship("Simulacro", backref="reviews")
    usuario = relationship("Usuario", backref="reviews_creadas")
