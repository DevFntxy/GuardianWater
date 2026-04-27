from sqlalchemy.ext.asyncio import AsyncSession
from models.mysql_models import Notificacion

TIPOS = {
    "nuevo_comentario": "Se añadió un comentario a tu reporte",
    "cambio_estado":    "El estado de tu reporte cambió",
    "reporte_resuelto": "Tu reporte ha sido resuelto",
    "reporte_rechazado":"Tu reporte ha sido rechazado",
    "nueva_zona":       "Se agregó una nueva zona de monitoreo",
    "alerta_sensor":    "Alerta de calidad del agua en tu zona",
}


async def crear_notificacion(db: AsyncSession, usuario_id: int, tipo: str, mensaje: str = None):
    notif = Notificacion(
        id_usuario=usuario_id,
        tipo=tipo,
        mensaje=mensaje or TIPOS.get(tipo, tipo),
    )
    db.add(notif)
    await db.flush()
    return notif


async def notificar_cambio_estado(db: AsyncSession, usuario_id: int, nuevo_estado: str, id_reporte: int):
    mensaje = f"Tu reporte #{id_reporte} cambió a estado: {nuevo_estado.replace('_', ' ')}"
    await crear_notificacion(db, usuario_id, "cambio_estado", mensaje)


async def notificar_nuevo_comentario(db: AsyncSession, usuario_id: int, id_reporte: int, autor: str):
    mensaje = f"{autor} comentó en tu reporte #{id_reporte}"
    await crear_notificacion(db, usuario_id, "nuevo_comentario", mensaje)
