from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError

from database import get_db
from models.mysql_models import Favorito, Reporte, Usuario
from services.auth_service import get_current_user

router = APIRouter()


@router.get("/")
async def listar_favoritos(
    usuario: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Favorito)
        .options(selectinload(Favorito.reporte).selectinload(Reporte.usuario))
        .where(Favorito.id_usuario == usuario.id_usuario)
        .order_by(Favorito.created_at.desc())
    )
    favoritos = result.scalars().all()
    return [
        {
            "id_favorito": f.id_favorito,
            "id_reporte": f.id_reporte,
            "created_at": f.created_at,
            "reporte": {
                "tipo": f.reporte.tipo,
                "descripcion": f.reporte.descripcion,
                "estado": f.reporte.estado,
            },
        }
        for f in favoritos
    ]


@router.post("/{id_reporte}", status_code=201)
async def agregar_favorito(
    id_reporte: int,
    usuario: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    r = await db.execute(select(Reporte).where(Reporte.id_reporte == id_reporte))
    if not r.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Reporte no encontrado")

    favorito = Favorito(id_usuario=usuario.id_usuario, id_reporte=id_reporte)
    db.add(favorito)
    try:
        await db.flush()
    except IntegrityError:
        raise HTTPException(status_code=409, detail="Ya está en favoritos")
    return {"message": "Agregado a favoritos"}


@router.delete("/{id_reporte}", status_code=204)
async def quitar_favorito(
    id_reporte: int,
    usuario: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Favorito).where(
            Favorito.id_usuario == usuario.id_usuario,
            Favorito.id_reporte == id_reporte,
        )
    )
    favorito = result.scalar_one_or_none()
    if not favorito:
        raise HTTPException(status_code=404, detail="No está en favoritos")
    await db.delete(favorito)
