from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import uuid4

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from config import settings
from database import get_db
from models.mysql_models import Usuario, Sesion

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer()


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def _create_token(data: dict, expires_delta: timedelta) -> str:
    payload = data.copy()
    payload.update({
        "exp": datetime.now(timezone.utc) + expires_delta,
        "iat": datetime.now(timezone.utc),
        "jti": str(uuid4()),
    })
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_access_token(usuario_id: int, rol: str) -> str:
    return _create_token(
        {"sub": str(usuario_id), "rol": rol, "type": "access"},
        timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )


def create_refresh_token(usuario_id: int) -> tuple[str, str]:
    jti = str(uuid4())
    expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": str(usuario_id),
        "type": "refresh",
        "exp": datetime.now(timezone.utc) + expires,
        "iat": datetime.now(timezone.utc),
        "jti": jti,
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token, jti


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> Usuario:
    payload = decode_token(credentials.credentials)
    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Tipo de token incorrecto")

    usuario_id = int(payload["sub"])
    result = await db.execute(
        select(Usuario)
        .options(selectinload(Usuario.rol))
        .where(Usuario.id_usuario == usuario_id, Usuario.activo == True)
    )
    usuario = result.scalar_one_or_none()
    if not usuario:
        raise HTTPException(status_code=401, detail="Usuario no encontrado o inactivo")
    return usuario


async def get_admin_user(usuario: Usuario = Depends(get_current_user)) -> Usuario:
    if usuario.rol.nombre != "admin":
        raise HTTPException(status_code=403, detail="Se requieren permisos de administrador")
    return usuario


async def authenticate_user(email: str, password: str, db: AsyncSession) -> Optional[Usuario]:
    result = await db.execute(
        select(Usuario)
        .options(selectinload(Usuario.rol))
        .where(Usuario.email == email)
    )
    usuario = result.scalar_one_or_none()
    if not usuario or not verify_password(password, usuario.password_hash):
        return None
    if not usuario.activo:
        raise HTTPException(status_code=403, detail="Cuenta desactivada")
    return usuario


async def save_refresh_session(usuario_id: int, jti: str, db: AsyncSession):
    expires = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    sesion = Sesion(id_usuario=usuario_id, token_jti=jti, expires_at=expires)
    db.add(sesion)
    await db.flush()


async def invalidate_session(jti: str, db: AsyncSession):
    result = await db.execute(select(Sesion).where(Sesion.token_jti == jti))
    sesion = result.scalar_one_or_none()
    if sesion:
        sesion.activa = False
        await db.flush()
