from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3307
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = "1234"
    MYSQL_DB: str = "guardianwater"

    MONGO_URI: str = "mongodb://localhost:27017"
    MONGO_DB: str = "guardianwater_nosql"

    SECRET_KEY: str = "cambiar-en-produccion-secreto-muy-largo"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:4200",
        "http://localhost:3000",
    ]

    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE_MB: int = 5

    class Config:
        env_file = ".env"


settings = Settings()
