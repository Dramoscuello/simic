from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.config import Base

class Grupo(Base):
    __tablename__ = "grupos"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), nullable=False)
    institucion_id = Column(Integer, ForeignKey("instituciones.id"), nullable=False)
    sede_id = Column(Integer, ForeignKey("sedes.id"), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relaciones
    institucion = relationship("Institucion", backref="grupos")
    sede = relationship("Sede", backref="grupos")
    # Nota: La relación 'estudiantes' se define en el modelo Usuario mediante backref
