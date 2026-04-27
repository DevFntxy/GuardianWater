"""Configuración global de logging para la API."""
import logging
import os
from logging.handlers import RotatingFileHandler

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

# Configurar el logger
logger = logging.getLogger("GuardianWater")
logger.setLevel(logging.INFO)

# Formateador de los logs
formatter = logging.Formatter(
    fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# File Handler con rotación (10 MB máximo, retiene 5 archivos)
log_file = os.path.join(LOG_DIR, "api.log")
file_handler = RotatingFileHandler(
    log_file,
    maxBytes=10 * 1024 * 1024,
    backupCount=5,
    encoding="utf-8"
)
file_handler.setFormatter(formatter)

# Stream Handler (para ver en consola)
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

# Agregar manejadores al logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)
