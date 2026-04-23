from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from database import get_db
from models.mysql_models import Usuario, Sesion
from schemas.auth import LoginRequest, TokenResponse, RefreshRequest
from schemas.usuario import UsuarioCreate, UsuarioOut
from services.auth_service import (
    authenticate_user, create_access_token, create_refresh_token,
    save_refresh_session, decode_token, hash_password, get_current_user,
)

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    usuario = await authenticate_user(data.email, data.password, db)
    if not usuario:
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")

    access_token = create_access_token(usuario.id_usuario, usuario.rol.nombre)
    refresh_token, jti = create_refresh_token(usuario.id_usuario)
    await save_refresh_session(usuario.id_usuario, jti, db)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        usuario=UsuarioOut.model_validate(usuario),
    )


@router.post("/registro", response_model=TokenResponse, status_code=201)
async def registro(data: UsuarioCreate, db: AsyncSession = Depends(get_db)):
    existe = await db.execute(select(Usuario).where(Usuario.email == data.email))
    if existe.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="El email ya está registrado")

    usuario = Usuario(
        nombre=data.nombre,
        apellido=data.apellido,
        email=data.email,
        password_hash=hash_password(data.password),
        telefono=data.telefono,
        colonia=data.colonia,
        municipio=data.municipio,
        estado=data.estado,
        id_rol=2,
    )
    db.add(usuario)
    await db.flush()
    await db.refresh(usuario, ["rol"])

    access_token = create_access_token(usuario.id_usuario, usuario.rol.nombre)
    refresh_token, jti = create_refresh_token(usuario.id_usuario)
    await save_refresh_session(usuario.id_usuario, jti, db)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        usuario=UsuarioOut.model_validate(usuario),
    )


@router.post("/refresh")
async def refresh_token(data: RefreshRequest, db: AsyncSession = Depends(get_db)):
    payload = decode_token(data.refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Token de refresco inválido")

    jti = payload.get("jti")
    result = await db.execute(
        select(Sesion).where(Sesion.token_jti == jti, Sesion.activa == True)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=401, detail="Sesión inválida o cerrada")

    usuario_id = int(payload["sub"])
    result = await db.execute(
        select(Usuario).options(selectinload(Usuario.rol)).where(Usuario.id_usuario == usuario_id)
    )
    usuario = result.scalar_one_or_none()
    if not usuario or not usuario.activo:
        raise HTTPException(status_code=401, detail="Usuario inactivo")

    new_access = create_access_token(usuario_id, usuario.rol.nombre)
    return {"access_token": new_access, "token_type": "bearer"}


@router.post("/logout")
async def logout(
    usuario: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Sesion).where(Sesion.id_usuario == usuario.id_usuario, Sesion.activa == True)
    )
    for sesion in result.scalars().all():
        sesion.activa = False
    return {"message": "Sesión cerrada correctamente"}
