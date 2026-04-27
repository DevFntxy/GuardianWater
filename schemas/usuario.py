from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import datetime


class UsuarioBase(BaseModel):
    nombre: str
    apellido: str
    email: EmailStr
    telefono: Optional[str] = None
    colonia: Optional[str] = None
    municipio: Optional[str] = None
    estado: Optional[str] = None


class UsuarioCreate(UsuarioBase):
    password: str

    @field_validator("password")
    @classmethod
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError("La contraseña debe tener al menos 8 caracteres")
        return v


class UsuarioUpdate(BaseModel):
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    telefono: Optional[str] = None
    colonia: Optional[str] = None
    municipio: Optional[str] = None
    estado: Optional[str] = None


class UsuarioPasswordUpdate(BaseModel):
    password_actual: str
    password_nuevo: str

    @field_validator("password_nuevo")
    @classmethod
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError("La contraseña debe tener al menos 8 caracteres")
        return v


class RolOut(BaseModel):
    id_rol: int
    nombre: str
    model_config = {"from_attributes": True}


class UsuarioOut(UsuarioBase):
    id_usuario: int
    id_rol: int
    rol: RolOut
    activo: bool
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class UsuarioPublico(BaseModel):
    id_usuario: int
    nombre: str
    apellido: str
    model_config = {"from_attributes": True}
