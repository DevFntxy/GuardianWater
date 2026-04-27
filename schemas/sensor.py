from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ParametrosSensor(BaseModel):
    ph: Optional[float] = None
    turbidez_ntu: Optional[float] = None
    temperatura_c: Optional[float] = None
    conductividad: Optional[float] = None
    cloro_libre: Optional[float] = None
    coliformes: Optional[float] = None


class SensorReadingCreate(BaseModel):
    zona_id: int
    dispositivo_id: str
    parametros: ParametrosSensor


class SensorReadingOut(BaseModel):
    id: str
    zona_id: int
    dispositivo_id: str
    timestamp: datetime
    parametros: ParametrosSensor
    calidad_calculada: int
    alerta: bool
    parametros_fuera_rango: List[str] = []
