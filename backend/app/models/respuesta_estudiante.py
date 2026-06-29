from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, DateTime, DECIMAL
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB
from app.database.config import Base


class RespuestaEstudiante(Base):
    """
    Almacena las respuestas de cada estudiante a un simulacro.
    
    El campo 'respuestas_detalladas' (JSONB) es CRÍTICO para los informes IA,
    contiene la estructura que N8N/LLM usa para generar análisis personalizados.
    
    Estructura de respuestas_detalladas:
    {
        "1": {
            "respuesta": "B",
            "competencia": "Interpretación y representación",
            "componente": "Numérico-variacional",
            "tema": "Porcentajes y proporciones",
            "acierto": true,
            "respuesta_correcta": "B"
        },
        "2": { ... }
    }
    """
    __tablename__ = "respuestas_estudiantes"

    id = Column(Integer, primary_key=True, index=True)
    
    # Relaciones principales
    simulacro_id = Column(Integer, ForeignKey("simulacros.id"), nullable=False)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    institucion_id = Column(Integer, ForeignKey("instituciones.id"), nullable=False)
    
    # Respuestas simples: {"1": "B", "2": "A", "3": "C", ...}
    respuestas = Column(JSONB, nullable=False)
    
    # Respuestas detalladas con metadatos (usado por LLM para informes)
    respuestas_detalladas = Column(JSONB, nullable=False)
    
    # Resultados calculados
    total_correctas = Column(Integer, default=0)
    total_incorrectas = Column(Integer, default=0)
    puntaje_total = Column(DECIMAL(5, 2), nullable=True)  # Porcentaje ej: 73.33
    
    # Timing
    tiempo_empleado = Column(Integer, nullable=True)  # Segundos
    fecha_inicio = Column(DateTime(timezone=True), nullable=True)
    fecha_finalizacion = Column(DateTime(timezone=True), nullable=True)
    
    # Estado de procesamiento
    notificado = Column(Boolean, default=False)  # Si se envió notificación al estudiante
    informe_generado = Column(Boolean, default=False)  # Si N8N/Backend ya generó el informe
    informe_url = Column(Text, nullable=True)  # Link a Google Drive del informe (Legacy)
    analisis_ia = Column(JSONB, nullable=True) # JSON completo del análisis generado por Groq
    fraude = Column(Boolean, default=False)  # Indica si el estudiante cometió fraude (window focus lost)

    # Reset lógico / Anulación
    anulado = Column(Boolean, default=False, nullable=False)
    reset_at = Column(DateTime(timezone=True), nullable=True)
    reset_by = Column(Integer, nullable=True)
    reset_reason = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relaciones
    simulacro = relationship("Simulacro", backref="respuestas_estudiantes")
    usuario = relationship("Usuario", backref="respuestas_estudiantes")
    institucion = relationship("Institucion", backref="respuestas_estudiantes")

    # Índices: Se crean a nivel de migración Alembic
    # idx_respuestas_estudiante -> usuario_id
    # idx_respuestas_simulacro -> simulacro_id
    # idx_respuestas_institucion -> institucion_id
    # idx_respuestas_notificado -> notificado (para N8N query)
    # idx_respuestas_fecha -> created_at

    # Constraint: Un estudiante solo puede responder un simulacro UNA vez
    # UNIQUE(simulacro_id, usuario_id) - Se define en migración Alembic
