from pydantic import BaseModel
from datetime import datetime


class ComentarioCreate(BaseModel):
    id_reporte: int
    contenido: str


class NotificacionOut(BaseModel):
    id_notificacion: int
    tipo: str
    mensaje: str
    leida: bool
    created_at: datetime
    model_config = {"from_attributes": True}
