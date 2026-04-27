from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from database import get_db
from models.mysql_models import Usuario, Reporte, Zona
from services.auth_service import get_admin_user
from services.notificacion_service import notificar_cambio_estado

router = APIRouter()


@router.get("/usuarios")
async def listar_usuarios(
    pagina: int = 1,
    por_pagina: int = 20,
    activo: bool = None,
    admin: Usuario = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    q = select(Usuario).options(selectinload(Usuario.rol)).order_by(Usuario.created_at.desc())
    if activo is not None:
        q = q.where(Usuario.activo == activo)

    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar()
    usuarios = (await db.execute(q.offset((pagina - 1) * por_pagina).limit(por_pagina))).scalars().all()

    return {
        "total": total,
        "pagina": pagina,
        "por_pagina": por_pagina,
        "items": [
            {
                "id_usuario": u.id_usuario,
                "nombre": u.nombre,
                "apellido": u.apellido,
                "email": u.email,
                "rol": u.rol.nombre,
                "activo": u.activo,
                "municipio": u.municipio,
                "created_at": u.created_at,
            }
            for u in usuarios
        ],
    }


@router.patch("/usuarios/{id_usuario}/estado")
async def cambiar_estado_usuario(
    id_usuario: int,
    data: dict,
    admin: Usuario = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Usuario).where(Usuario.id_usuario == id_usuario))
    usuario = result.scalar_one_or_none()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    if id_usuario == admin.id_usuario:
        raise HTTPException(status_code=400, detail="No puedes modificar tu propia cuenta")

    if "activo" in data:
        usuario.activo = data["activo"]
    if "id_rol" in data:
        usuario.id_rol = data["id_rol"]
    return {"message": "Usuario actualizado correctamente"}


@router.patch("/reportes/{id_reporte}/estado")
async def cambiar_estado_reporte(
    id_reporte: int,
    data: dict,
    admin: Usuario = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Reporte).where(Reporte.id_reporte == id_reporte))
    reporte = result.scalar_one_or_none()
    if not reporte:
        raise HTTPException(status_code=404, detail="Reporte no encontrado")

    estados_validos = {"pendiente", "en_revision", "resuelto", "rechazado"}
    nuevo_estado = data.get("estado")
    if nuevo_estado not in estados_validos:
        raise HTTPException(status_code=422, detail=f"Estado inválido. Opciones: {estados_validos}")

    reporte.estado = nuevo_estado
    await db.flush()
    await notificar_cambio_estado(db, reporte.id_usuario, nuevo_estado, id_reporte)
    return {"message": f"Estado actualizado a: {nuevo_estado}"}


@router.get("/stats")
async def estadisticas_generales(
    admin: Usuario = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    total_usuarios  = (await db.execute(select(func.count()).select_from(Usuario))).scalar()
    total_reportes  = (await db.execute(select(func.count()).select_from(Reporte))).scalar()
    pendientes      = (await db.execute(select(func.count()).select_from(Reporte).where(Reporte.estado == "pendiente"))).scalar()
    en_revision     = (await db.execute(select(func.count()).select_from(Reporte).where(Reporte.estado == "en_revision"))).scalar()
    resueltos       = (await db.execute(select(func.count()).select_from(Reporte).where(Reporte.estado == "resuelto"))).scalar()
    rechazados      = (await db.execute(select(func.count()).select_from(Reporte).where(Reporte.estado == "rechazado"))).scalar()

    return {
        "total_usuarios": total_usuarios,
        "total_reportes": total_reportes,
        "reportes_pendientes": pendientes,
        "reportes_en_revision": en_revision,
        "reportes_resueltos": resueltos,
        "reportes_rechazados": rechazados,
    }


@router.post("/zonas", status_code=201)
async def crear_zona(
    data: dict,
    admin: Usuario = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    zona = Zona(
        nombre=data["nombre"],
        descripcion=data.get("descripcion"),
        municipio=data.get("municipio"),
        estado=data.get("estado"),
        latitud=data.get("latitud"),
        longitud=data.get("longitud"),
    )
    db.add(zona)
    await db.flush()
    return {"id_zona": zona.id_zona, "message": "Zona creada exitosamente"}


@router.patch("/zonas/{id_zona}")
async def actualizar_zona(
    id_zona: int,
    data: dict,
    admin: Usuario = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Zona).where(Zona.id_zona == id_zona))
    zona = result.scalar_one_or_none()
    if not zona:
        raise HTTPException(status_code=404, detail="Zona no encontrada")
    for field in ("nombre", "descripcion", "municipio", "estado", "latitud", "longitud", "activa"):
        if field in data:
            setattr(zona, field, data[field])
    return {"message": "Zona actualizada correctamente"}
