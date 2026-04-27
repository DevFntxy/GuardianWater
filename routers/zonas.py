from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db
from models.mysql_models import Zona, Usuario
from services.auth_service import get_current_user

router = APIRouter()


@router.get("/")
async def listar_zonas(
    usuario: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Zona).where(Zona.activa == True).order_by(Zona.nombre)
    )
    return result.scalars().all()


@router.get("/{id_zona}")
async def obtener_zona(
    id_zona: int,
    usuario: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Zona).where(Zona.id_zona == id_zona))
    zona = result.scalar_one_or_none()
    if not zona:
        raise HTTPException(status_code=404, detail="Zona no encontrada")
    return zona
