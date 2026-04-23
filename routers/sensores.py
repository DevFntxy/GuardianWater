from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timezone

from database import get_mongo_db
from models.mysql_models import Usuario
from services.auth_service import get_current_user

router = APIRouter()

LIMITES = {
    "ph":            (6.5, 8.5),
    "turbidez_ntu":  (0.0, 4.0),
    "temperatura_c": (5.0, 35.0),
    "conductividad": (0.0, 1500.0),
    "cloro_libre":   (0.2, 2.0),
    "coliformes":    (0.0, 0.0),
}


def calcular_calidad(parametros: dict) -> tuple[int, list]:
    fuera_rango = [
        param for param, (mn, mx) in LIMITES.items()
        if (v := parametros.get(param)) is not None and not (mn <= v <= mx)
    ]
    return max(1, 5 - len(fuera_rango)), fuera_rango


@router.post("/lecturas", status_code=201)
async def registrar_lectura(
    data: dict,
    usuario: Usuario = Depends(get_current_user),
):
    mongo = get_mongo_db()
    parametros = data.get("parametros", {})
    calidad, fuera = calcular_calidad(parametros)

    doc = {
        "zona_id": data["zona_id"],
        "dispositivo_id": data.get("dispositivo_id", "manual"),
        "timestamp": datetime.now(timezone.utc),
        "parametros": parametros,
        "calidad_calculada": calidad,
        "alerta": len(fuera) > 0,
        "parametros_fuera_rango": fuera,
    }
    result = await mongo.sensor_readings.insert_one(doc)
    return {"id": str(result.inserted_id), "calidad": calidad, "alerta": doc["alerta"]}


@router.get("/{zona_id}/ultimas")
async def ultimas_lecturas(
    zona_id: int,
    limite: int = 20,
    usuario: Usuario = Depends(get_current_user),
):
    mongo = get_mongo_db()
    cursor = (
        mongo.sensor_readings
        .find({"zona_id": zona_id}, {"_id": 1, "timestamp": 1, "parametros": 1,
                                      "calidad_calculada": 1, "alerta": 1,
                                      "parametros_fuera_rango": 1})
        .sort("timestamp", -1)
        .limit(limite)
    )
    lecturas = []
    async for doc in cursor:
        doc["id"] = str(doc.pop("_id"))
        lecturas.append(doc)
    return lecturas


@router.get("/{zona_id}/estadisticas")
async def estadisticas_zona(
    zona_id: int,
    usuario: Usuario = Depends(get_current_user),
):
    mongo = get_mongo_db()
    stats = await mongo.zona_stats.find_one({"zona_id": zona_id}, {"_id": 0})
    if not stats:
        raise HTTPException(status_code=404, detail="Sin estadísticas para esta zona")
    return stats
