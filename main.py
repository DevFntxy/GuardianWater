"""Main application module for GuardianWater API."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from config import settings
from database import init_db
from logger import logger
from routers import auth, usuarios, reportes, zonas, comentarios, favoritos, sensores, admin
from middlewares.logging_middleware import ActivityLogMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan processes like DB connection."""
    logger.info("Iniciando aplicación y conectando a la base de datos...")
    await init_db()
    logger.info("Base de datos inicializada correctamente.")
    yield
    logger.info("Apagando la aplicación...")


app = FastAPI(
    title="GuardianWater API",
    description="Backend para monitoreo de calidad del agua",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(ActivityLogMiddleware)

app.include_router(auth.router,        prefix="/api/auth",        tags=["Auth"])
app.include_router(usuarios.router,    prefix="/api/usuarios",    tags=["Usuarios"])
app.include_router(reportes.router,    prefix="/api/reportes",    tags=["Reportes"])
app.include_router(zonas.router,       prefix="/api/zonas",       tags=["Zonas"])
app.include_router(comentarios.router, prefix="/api/comentarios", tags=["Comentarios"])
app.include_router(favoritos.router,   prefix="/api/favoritos",   tags=["Favoritos"])
app.include_router(sensores.router,    prefix="/api/sensores",    tags=["Sensores"])
app.include_router(admin.router,       prefix="/api/admin",       tags=["Admin"])


@app.get("/api/health")
async def health_check():
    """Health check endpoint to verify API status."""
    return {"status": "ok", "service": "guardianwater-api"}
