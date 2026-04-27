from pydantic import BaseModel
from typing import Optional


class ZonaCreate(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    municipio: Optional[str] = None
    estado: Optional[str] = None
    latitud: Optional[float] = None
    longitud: Optional[float] = None


class ZonaOut(BaseModel):
    id_zona: int
    nombre: str
    descripcion: Optional[str]
    municipio: Optional[str]
    estado: Optional[str]
    latitud: Optional[float]
    longitud: Optional[float]
    activa: bool
    model_config = {"from_attributes": True}
