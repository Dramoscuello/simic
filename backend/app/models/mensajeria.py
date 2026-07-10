from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB
from app.database.config import Base
import enum

class MessageType(str, enum.Enum):
    TEXTO = "texto"
    SOLICITUD_SIMULACRO = "solicitud_simulacro"
    COMPROBANTE_PAGO = "comprobante_pago"  # Nuevo tipo para adjuntar comprobantes

class Conversacion(Base):
    __tablename__ = "conversaciones"

    id = Column(Integer, primary_key=True, index=True)
    institucion_id = Column(Integer, ForeignKey("instituciones.id"), nullable=False, index=True)
    participante_1_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True, index=True)
    participante_2_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True, index=True)
    asunto = Column(String(255), nullable=True)
    estado = Column(String(50), default="abierta") # abierta, cerrada
    
    ultimo_mensaje_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    institucion = relationship("Institucion", backref="conversaciones")
    participante_1 = relationship("Usuario", foreign_keys=[participante_1_id])
    participante_2 = relationship("Usuario", foreign_keys=[participante_2_id])
    mensajes = relationship("Mensaje", back_populates="conversacion", cascade="all, delete-orphan", order_by="Mensaje.created_at")

class Mensaje(Base):
    __tablename__ = "mensajes"

    id = Column(Integer, primary_key=True, index=True)
    conversacion_id = Column(Integer, ForeignKey("conversaciones.id"), nullable=False)
    remitente_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    
    tipo = Column(String(50), default="texto") # texto, solicitud_simulacro, comprobante_pago
    contenido = Column(Text, nullable=True) # Texto normal
    metadata_msg = Column(JSONB, nullable=True) # Datos extra (areas, num_preguntas, verificado, monto, etc.)
    
    # Nuevo: Imagen adjunta en Base64 (para comprobantes de pago)
    imagen_adjunto = Column(Text, nullable=True)
    
    leido = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    conversacion = relationship("Conversacion", back_populates="mensajes")
    remitente = relationship("Usuario") # Para saber quien lo envió (nombre, rol)

