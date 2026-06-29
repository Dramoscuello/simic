from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, Index, desc
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.config import Base


class Notificacion(Base):
    __tablename__ = "notificaciones"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, index=True)
    institucion_id = Column(Integer, ForeignKey("instituciones.id"), nullable=True, index=True)
    tipo = Column(String(50), nullable=False, index=True)
    titulo = Column(String(255), nullable=False)
    mensaje = Column(Text, nullable=False)
    payload_json = Column(JSONB, nullable=True)
    leida = Column(Boolean, nullable=False, default=False, index=True)
    leida_at = Column(DateTime(timezone=True), nullable=True)
    actor_usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    event_key = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    usuario = relationship("Usuario", foreign_keys=[usuario_id], backref="notificaciones")
    actor_usuario = relationship("Usuario", foreign_keys=[actor_usuario_id])
    institucion = relationship("Institucion", backref="notificaciones")

    __table_args__ = (
        UniqueConstraint("usuario_id", "event_key", name="uq_notificaciones_usuario_event_key"),
        Index("ix_notificaciones_usuario_leida_created_at", "usuario_id", "leida", desc("created_at")),
        Index("ix_notificaciones_usuario_created_at", "usuario_id", desc("created_at")),
    )
