from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class NotificacionOut(BaseModel):
    id: int
    tipo: str
    titulo: str
    mensaje: str
    payload_json: Optional[dict] = None
    leida: bool
    leida_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class UnreadCountOut(BaseModel):
    unread_count: int


class MarkAllReadOut(BaseModel):
    updated_count: int
