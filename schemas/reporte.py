from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import datetime
from enum import Enum
from schemas.usuario import UsuarioPublico


class TipoReporteEnum(str, Enum):
    problema = "problema"
    comentario = "comentario"
    desconocido = "desconocido"


class EstadoReporteEnum(str, Enum):
    pendiente = "pendiente"
    en_revision = "en_revision"
    resuelto = "resuelto"
    rechazado = "rechazado"


class ReporteCreate(BaseModel):
    id_zona: Optional[int] = None
    tipo: TipoReporteEnum = TipoReporteEnum.problema
    descripcion: str
    calidad_estimada: Optional[int] = None
    latitud: Optional[float] = None
    longitud: Optional[float] = None

    @field_validator("calidad_estimada")
    @classmethod
    def calidad_rango(cls, v):
        if v is not None and not (1 <= v <= 5):
            raise ValueError("calidad_estimada debe estar entre 1 y 5")
        return v


class ReporteUpdate(BaseModel):
    estado: Optional[EstadoReporteEnum] = None
    descripcion: Optional[str] = None


class ComentarioOut(BaseModel):
    id_comentario: int
    contenido: str
    created_at: datetime
    usuario: UsuarioPublico
    model_config = {"from_attributes": True}


class ReporteOut(BaseModel):
    id_reporte: int
    tipo: TipoReporteEnum
    descripcion: str
    estado: EstadoReporteEnum
    calidad_estimada: Optional[int]
    latitud: Optional[float]
    longitud: Optional[float]
    imagen_url: Optional[str]
    created_at: datetime
    updated_at: datetime
    usuario: UsuarioPublico
    id_zona: Optional[int]
    es_favorito: bool = False
    total_comentarios: int = 0
    model_config = {"from_attributes": True}


class ReporteDetalle(ReporteOut):
    comentarios: List[ComentarioOut] = []


class PaginatedReportes(BaseModel):
    total: int
    pagina: int
    por_pagina: int
    items: List[ReporteOut]
