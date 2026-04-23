from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db
from models.mysql_models import Comentario, Reporte, Usuario
from schemas.notificacion import ComentarioCreate
from services.auth_service import get_current_user
from services.notificacion_service import notificar_nuevo_comentario

router = APIRouter()


@router.post("/", status_code=201)
async def crear_comentario(
    data: ComentarioCreate,
    usuario: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Reporte).where(Reporte.id_reporte == data.id_reporte))
    reporte = result.scalar_one_or_none()
    if not reporte:
        raise HTTPException(status_code=404, detail="Reporte no encontrado")

    comentario = Comentario(
        id_reporte=data.id_reporte,
        id_usuario=usuario.id_usuario,
        contenido=data.contenido.strip(),
    )
    db.add(comentario)
    await db.flush()

    if reporte.id_usuario != usuario.id_usuario:
        await notificar_nuevo_comentario(
            db, reporte.id_usuario, data.id_reporte,
            f"{usuario.nombre} {usuario.apellido}"
        )

    return {"id_comentario": comentario.id_comentario, "message": "Comentario agregado"}


@router.delete("/{id_comentario}", status_code=204)
async def eliminar_comentario(
    id_comentario: int,
    usuario: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Comentario).where(Comentario.id_comentario == id_comentario)
    )
    comentario = result.scalar_one_or_none()
    if not comentario:
        raise HTTPException(status_code=404, detail="Comentario no encontrado")
    if comentario.id_usuario != usuario.id_usuario and usuario.rol.nombre != "admin":
        raise HTTPException(status_code=403, detail="Sin permisos")
    await db.delete(comentario)
