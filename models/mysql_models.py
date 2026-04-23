from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime,
    ForeignKey, Enum, DECIMAL, SmallInteger, UniqueConstraint
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
import enum

Base = declarative_base()


class TipoReporte(str, enum.Enum):
    problema = "problema"
    comentario = "comentario"
    desconocido = "desconocido"


class EstadoReporte(str, enum.Enum):
    pendiente = "pendiente"
    en_revision = "en_revision"
    resuelto = "resuelto"
    rechazado = "rechazado"


class Rol(Base):
    __tablename__ = "rol"

    id_rol      = Column(Integer, primary_key=True, autoincrement=True)
    nombre      = Column(String(50), nullable=False, unique=True)
    descripcion = Column(Text)

    usuarios = relationship("Usuario", back_populates="rol")


class Usuario(Base):
    __tablename__ = "usuario"

    id_usuario    = Column(Integer, primary_key=True, autoincrement=True)
    id_rol        = Column(Integer, ForeignKey("rol.id_rol"), nullable=False, default=2)
    nombre        = Column(String(100), nullable=False)
    apellido      = Column(String(100), nullable=False)
    email         = Column(String(150), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    telefono      = Column(String(20))
    colonia       = Column(String(120))
    municipio     = Column(String(120))
    estado        = Column(String(80))
    activo        = Column(Boolean, nullable=False, default=True)
    created_at    = Column(DateTime, nullable=False, server_default=func.now())
    updated_at    = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    rol            = relationship("Rol", back_populates="usuarios")
    reportes       = relationship("Reporte", back_populates="usuario")
    comentarios    = relationship("Comentario", back_populates="usuario")
    favoritos      = relationship("Favorito", back_populates="usuario")
    notificaciones = relationship("Notificacion", back_populates="usuario")
    sesiones       = relationship("Sesion", back_populates="usuario")


class Zona(Base):
    __tablename__ = "zona"

    id_zona     = Column(Integer, primary_key=True, autoincrement=True)
    nombre      = Column(String(150), nullable=False)
    descripcion = Column(Text)
    municipio   = Column(String(120))
    estado      = Column(String(80))
    latitud     = Column(DECIMAL(10, 7))
    longitud    = Column(DECIMAL(10, 7))
    activa      = Column(Boolean, nullable=False, default=True)

    reportes = relationship("Reporte", back_populates="zona")


class Reporte(Base):
    __tablename__ = "reporte"

    id_reporte       = Column(Integer, primary_key=True, autoincrement=True)
    id_usuario       = Column(Integer, ForeignKey("usuario.id_usuario"), nullable=False)
    id_zona          = Column(Integer, ForeignKey("zona.id_zona"), nullable=True)
    tipo             = Column(Enum(TipoReporte), nullable=False, default=TipoReporte.problema)
    descripcion      = Column(Text, nullable=False)
    estado           = Column(Enum(EstadoReporte), nullable=False, default=EstadoReporte.pendiente)
    calidad_estimada = Column(SmallInteger)
    latitud          = Column(DECIMAL(10, 7))
    longitud         = Column(DECIMAL(10, 7))
    imagen_url       = Column(String(500))
    created_at       = Column(DateTime, nullable=False, server_default=func.now())
    updated_at       = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    usuario     = relationship("Usuario", back_populates="reportes")
    zona        = relationship("Zona", back_populates="reportes")
    comentarios = relationship("Comentario", back_populates="reporte", cascade="all, delete-orphan")
    favoritos   = relationship("Favorito", back_populates="reporte", cascade="all, delete-orphan")


class Comentario(Base):
    __tablename__ = "comentario"

    id_comentario = Column(Integer, primary_key=True, autoincrement=True)
    id_reporte    = Column(Integer, ForeignKey("reporte.id_reporte", ondelete="CASCADE"), nullable=False)
    id_usuario    = Column(Integer, ForeignKey("usuario.id_usuario"), nullable=False)
    contenido     = Column(Text, nullable=False)
    created_at    = Column(DateTime, nullable=False, server_default=func.now())

    reporte = relationship("Reporte", back_populates="comentarios")
    usuario = relationship("Usuario", back_populates="comentarios")


class Favorito(Base):
    __tablename__ = "favorito"
    __table_args__ = (UniqueConstraint("id_usuario", "id_reporte"),)

    id_favorito = Column(Integer, primary_key=True, autoincrement=True)
    id_usuario  = Column(Integer, ForeignKey("usuario.id_usuario", ondelete="CASCADE"), nullable=False)
    id_reporte  = Column(Integer, ForeignKey("reporte.id_reporte", ondelete="CASCADE"), nullable=False)
    created_at  = Column(DateTime, nullable=False, server_default=func.now())

    usuario = relationship("Usuario", back_populates="favoritos")
    reporte = relationship("Reporte", back_populates="favoritos")


class Notificacion(Base):
    __tablename__ = "notificacion"

    id_notificacion = Column(Integer, primary_key=True, autoincrement=True)
    id_usuario      = Column(Integer, ForeignKey("usuario.id_usuario", ondelete="CASCADE"), nullable=False)
    tipo            = Column(String(50), nullable=False)
    mensaje         = Column(Text, nullable=False)
    leida           = Column(Boolean, nullable=False, default=False)
    created_at      = Column(DateTime, nullable=False, server_default=func.now())

    usuario = relationship("Usuario", back_populates="notificaciones")


class Sesion(Base):
    __tablename__ = "sesion"

    id_sesion  = Column(Integer, primary_key=True, autoincrement=True)
    id_usuario = Column(Integer, ForeignKey("usuario.id_usuario", ondelete="CASCADE"), nullable=False)
    token_jti  = Column(String(36), nullable=False, unique=True)
    activa     = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    expires_at = Column(DateTime, nullable=False)

    usuario = relationship("Usuario", back_populates="sesiones")
