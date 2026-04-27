from pydantic import BaseModel, EmailStr
from schemas.usuario import UsuarioOut


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    usuario: UsuarioOut


class RefreshRequest(BaseModel):
    refresh_token: str
