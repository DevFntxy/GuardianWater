from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import Optional

from database import get_db
from models.mysql_models import Reporte, Favorito, Comentario, Usuario
from schemas.reporte import ReporteCreate
from services.auth_service import get_current_user

router = APIRouter()


@router.get("/")
async def listar_reportes(
    pagina: int = 1,
    por_pagina: int = 20,
    estado: Optional[str] = None,
    tipo: Optional[str] = None,
    id_zona: Optional[int] = None,
    usuario: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    q = (
        select(Reporte)
        .options(selectinload(Reporte.usuario), selectinload(Reporte.comentarios))
        .order_by(Reporte.created_at.desc())
    )
    if estado:
        q = q.where(Reporte.estado == estado)
    if tipo:
        q = q.where(Reporte.tipo == tipo)
    if id_zona:
        q = q.where(Reporte.id_zona == id_zona)

    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar()
    reportes = (await db.execute(q.offset((pagina - 1) * por_pagina).limit(por_pagina))).scalars().all()

    favs = {
        f for f in (
            await db.execute(
                select(Favorito.id_reporte).where(Favorito.id_usuario == usuario.id_usuario)
            )
        ).scalars().all()
    }

    items = [
        {
            "id_reporte": r.id_reporte,
            "tipo": r.tipo,
            "descripcion": r.descripcion,
            "estado": r.estado,
            "calidad_estimada": r.calidad_estimada,
            "latitud": float(r.latitud) if r.latitud else None,
            "longitud": float(r.longitud) if r.longitud else None,
            "imagen_url": r.imagen_url,
            "created_at": r.created_at,
            "updated_at": r.updated_at,
            "id_zona": r.id_zona,
            "es_favorito": r.id_reporte in favs,
            "total_comentarios": len(r.comentarios),
            "usuario": {
                "id_usuario": r.usuario.id_usuario,
                "nombre": r.usuario.nombre,
                "apellido": r.usuario.apellido,
            },
        }
        for r in reportes
    ]
    return {"total": total, "pagina": pagina, "por_pagina": por_pagina, "items": items}


@router.post("/", status_code=201)
async def crear_reporte(
    data: ReporteCreate,
    usuario: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    reporte = Reporte(
        id_usuario=usuario.id_usuario,
        id_zona=data.id_zona,
        tipo=data.tipo,
        descripcion=data.descripcion,
        calidad_estimada=data.calidad_estimada,
        latitud=data.latitud,
        longitud=data.longitud,
    )
    db.add(reporte)
    await db.flush()
    return {"id_reporte": reporte.id_reporte, "message": "Reporte creado exitosamente"}


@router.get("/{id_reporte}")
async def obtener_reporte(
    id_reporte: int,
    usuario: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Reporte)
        .options(
            selectinload(Reporte.usuario),
            selectinload(Reporte.comentarios).selectinload(Comentario.usuario),
        )
        .where(Reporte.id_reporte == id_reporte)
    )
    reporte = result.scalar_one_or_none()
    if not reporte:
        raise HTTPException(status_code=404, detail="Reporte no encontrado")

    fav = await db.execute(
        select(Favorito).where(
            Favorito.id_usuario == usuario.id_usuario,
            Favorito.id_reporte == id_reporte,
        )
    )
    es_favorito = fav.scalar_one_or_none() is not None

    return {
        "id_reporte": reporte.id_reporte,
        "tipo": reporte.tipo,
        "descripcion": reporte.descripcion,
        "estado": reporte.estado,
        "calidad_estimada": reporte.calidad_estimada,
        "latitud": float(reporte.latitud) if reporte.latitud else None,
        "longitud": float(reporte.longitud) if reporte.longitud else None,
        "imagen_url": reporte.imagen_url,
        "created_at": reporte.created_at,
        "updated_at": reporte.updated_at,
        "id_zona": reporte.id_zona,
        "es_favorito": es_favorito,
        "usuario": {
            "id_usuario": reporte.usuario.id_usuario,
            "nombre": reporte.usuario.nombre,
            "apellido": reporte.usuario.apellido,
        },
        "comentarios": [
            {
                "id_comentario": c.id_comentario,
                "contenido": c.contenido,
                "created_at": c.created_at,
                "usuario": {
                    "id_usuario": c.usuario.id_usuario,
                    "nombre": c.usuario.nombre,
                    "apellido": c.usuario.apellido,
                },
            }
            for c in reporte.comentarios
        ],
    }


@router.delete("/{id_reporte}", status_code=204)
async def eliminar_reporte(
    id_reporte: int,
    usuario: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Reporte).where(Reporte.id_reporte == id_reporte))
    reporte = result.scalar_one_or_none()
    if not reporte:
        raise HTTPException(status_code=404, detail="Reporte no encontrado")
    if reporte.id_usuario != usuario.id_usuario and usuario.rol.nombre != "admin":
        raise HTTPException(status_code=403, detail="Sin permisos para eliminar este reporte")
    await db.delete(reporte)
