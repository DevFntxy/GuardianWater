from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from database import get_db
from models.mysql_models import Usuario, Notificacion
from schemas.usuario import UsuarioOut, UsuarioUpdate
from services.auth_service import get_current_user

router = APIRouter()


@router.get("/me", response_model=UsuarioOut)
async def get_me(usuario: Usuario = Depends(get_current_user)):
    return UsuarioOut.model_validate(usuario)


@router.put("/me", response_model=UsuarioOut)
async def update_me(
    data: UsuarioUpdate,
    usuario: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(usuario, field, value)
    await db.flush()

    result = await db.execute(
        select(Usuario)
        .options(selectinload(Usuario.rol))
        .where(Usuario.id_usuario == usuario.id_usuario)
    )
    usuario = result.scalar_one()
    return UsuarioOut.model_validate(usuario)


@router.get("/me/notificaciones")
async def get_notificaciones(
    solo_no_leidas: bool = False,
    usuario: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    q = select(Notificacion).where(Notificacion.id_usuario == usuario.id_usuario)
    if solo_no_leidas:
        q = q.where(Notificacion.leida == False)
    q = q.order_by(Notificacion.created_at.desc()).limit(50)
    result = await db.execute(q)
    return result.scalars().all()


@router.patch("/me/notificaciones/marcar-leidas")
async def marcar_leidas(
    usuario: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Notificacion).where(
            Notificacion.id_usuario == usuario.id_usuario,
            Notificacion.leida == False,
        )
    )
    for n in result.scalars().all():
        n.leida = True
    return {"message": "Notificaciones marcadas como leídas"}