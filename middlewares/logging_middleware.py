import time
from datetime import datetime, timezone

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from database import get_mongo_db


class ActivityLogMiddleware(BaseHTTPMiddleware):
    """Registra cada petición HTTP en MongoDB activity_logs."""

    SKIP_PATHS = {"/api/health", "/docs", "/openapi.json", "/redoc"}

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path in self.SKIP_PATHS:
            return await call_next(request)

        start = time.time()
        response = await call_next(request)
        duration_ms = int((time.time() - start) * 1000)

        usuario_id = None
        try:
            auth = request.headers.get("authorization", "")
            if auth.startswith("Bearer "):
                from jose import jwt
                from config import settings
                payload = jwt.decode(
                    auth[7:],
                    settings.SECRET_KEY,
                    algorithms=[settings.ALGORITHM],
                    options={"verify_exp": False},
                )
                usuario_id = int(payload.get("sub", 0)) or None
        except Exception:
            pass

        log = {
            "usuario_id": usuario_id,
            "accion": f"{request.method} {request.url.path}",
            "recurso": request.url.path,
            "ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent", ""),
            "status_code": response.status_code,
            "duration_ms": duration_ms,
            "timestamp": datetime.now(timezone.utc),
            "detalle": {},
        }

        try:
            mongo = get_mongo_db()
            if mongo is not None:
                await mongo.activity_logs.insert_one(log)
        except Exception:
            pass  # El log nunca debe interrumpir el flujo principal

        return response
