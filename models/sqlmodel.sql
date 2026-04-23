-- ============================================================
-- GuardianWater — Esquema MySQL
-- Base de datos relacional para gestión de usuarios, reportes
-- de calidad de agua, zonas, comentarios y favoritos.
-- ============================================================

CREATE DATABASE IF NOT EXISTS guardianwater
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE guardianwater;

-- ------------------------------------------------------------
-- ROL
-- ------------------------------------------------------------
CREATE TABLE rol (
  id_rol      INT AUTO_INCREMENT PRIMARY KEY,
  nombre      VARCHAR(50) NOT NULL UNIQUE,  -- 'admin', 'usuario'
  descripcion TEXT
);

INSERT INTO rol (nombre, descripcion) VALUES
  ('admin',   'Administrador con acceso completo al sistema'),
  ('usuario', 'Usuario regular que puede crear y consultar reportes');

-- ------------------------------------------------------------
-- USUARIO
-- ------------------------------------------------------------
CREATE TABLE usuario (
  id_usuario    INT AUTO_INCREMENT PRIMARY KEY,
  id_rol        INT NOT NULL DEFAULT 2,
  nombre        VARCHAR(100) NOT NULL,
  apellido      VARCHAR(100) NOT NULL,
  email         VARCHAR(150) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  telefono      VARCHAR(20),
  colonia       VARCHAR(120),
  municipio     VARCHAR(120),
  estado        VARCHAR(80),
  activo        BOOLEAN NOT NULL DEFAULT TRUE,
  created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_usuario_rol FOREIGN KEY (id_rol) REFERENCES rol(id_rol)
);

CREATE INDEX idx_usuario_email   ON usuario(email);
CREATE INDEX idx_usuario_id_rol  ON usuario(id_rol);
CREATE INDEX idx_usuario_activo  ON usuario(activo);

-- ------------------------------------------------------------
-- ZONA
-- Áreas geográficas monitoreadas (colonias, municipios, etc.)
-- ------------------------------------------------------------
CREATE TABLE zona (
  id_zona     INT AUTO_INCREMENT PRIMARY KEY,
  nombre      VARCHAR(150) NOT NULL,
  descripcion TEXT,
  municipio   VARCHAR(120),
  estado      VARCHAR(80),
  latitud     DECIMAL(10, 7),
  longitud    DECIMAL(10, 7),
  activa      BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE INDEX idx_zona_municipio ON zona(municipio);
CREATE INDEX idx_zona_activa    ON zona(activa);

-- ------------------------------------------------------------
-- REPORTE
-- Reporte de calidad de agua creado por un usuario en una zona
-- ------------------------------------------------------------
CREATE TABLE reporte (
  id_reporte        INT AUTO_INCREMENT PRIMARY KEY,
  id_usuario        INT NOT NULL,
  id_zona           INT,
  -- Tipo: 'problema', 'comentario', 'desconocido' (icon_gem_*)
  tipo              ENUM('problema','comentario','desconocido') NOT NULL DEFAULT 'problema',
  descripcion       TEXT NOT NULL,
  -- Estado del reporte: pendiente, en_revision, resuelto, rechazado
  estado            ENUM('pendiente','en_revision','resuelto','rechazado') NOT NULL DEFAULT 'pendiente',
  calidad_estimada  TINYINT UNSIGNED CHECK (calidad_estimada BETWEEN 1 AND 5),
  latitud           DECIMAL(10, 7),
  longitud          DECIMAL(10, 7),
  imagen_url        VARCHAR(500),
  created_at        DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at        DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_reporte_usuario FOREIGN KEY (id_usuario) REFERENCES usuario(id_usuario),
  CONSTRAINT fk_reporte_zona    FOREIGN KEY (id_zona)    REFERENCES zona(id_zona)
);

CREATE INDEX idx_reporte_usuario    ON reporte(id_usuario);
CREATE INDEX idx_reporte_zona       ON reporte(id_zona);
CREATE INDEX idx_reporte_estado     ON reporte(estado);
CREATE INDEX idx_reporte_tipo       ON reporte(tipo);
CREATE INDEX idx_reporte_created_at ON reporte(created_at DESC);

-- ------------------------------------------------------------
-- COMENTARIO
-- Comentarios de usuarios sobre un reporte
-- ------------------------------------------------------------
CREATE TABLE comentario (
  id_comentario INT AUTO_INCREMENT PRIMARY KEY,
  id_reporte    INT NOT NULL,
  id_usuario    INT NOT NULL,
  contenido     TEXT NOT NULL,
  created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_comentario_reporte FOREIGN KEY (id_reporte) REFERENCES reporte(id_reporte) ON DELETE CASCADE,
  CONSTRAINT fk_comentario_usuario FOREIGN KEY (id_usuario) REFERENCES usuario(id_usuario)
);

CREATE INDEX idx_comentario_reporte ON comentario(id_reporte);
CREATE INDEX idx_comentario_usuario ON comentario(id_usuario);

-- ------------------------------------------------------------
-- FAVORITO
-- Reportes marcados como favoritos por un usuario
-- ------------------------------------------------------------
CREATE TABLE favorito (
  id_favorito INT AUTO_INCREMENT PRIMARY KEY,
  id_usuario  INT NOT NULL,
  id_reporte  INT NOT NULL,
  created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uq_favorito (id_usuario, id_reporte),
  CONSTRAINT fk_favorito_usuario FOREIGN KEY (id_usuario) REFERENCES usuario(id_usuario) ON DELETE CASCADE,
  CONSTRAINT fk_favorito_reporte FOREIGN KEY (id_reporte) REFERENCES reporte(id_reporte) ON DELETE CASCADE
);

CREATE INDEX idx_favorito_usuario ON favorito(id_usuario);

-- ------------------------------------------------------------
-- NOTIFICACION
-- Notificaciones internas para cada usuario
-- ------------------------------------------------------------
CREATE TABLE notificacion (
  id_notificacion INT AUTO_INCREMENT PRIMARY KEY,
  id_usuario      INT NOT NULL,
  tipo            VARCHAR(50) NOT NULL,  -- 'nuevo_reporte', 'cambio_estado', 'comentario', etc.
  mensaje         TEXT NOT NULL,
  leida           BOOLEAN NOT NULL DEFAULT FALSE,
  created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_notificacion_usuario FOREIGN KEY (id_usuario) REFERENCES usuario(id_usuario) ON DELETE CASCADE
);

CREATE INDEX idx_notificacion_usuario ON notificacion(id_usuario);
CREATE INDEX idx_notificacion_leida   ON notificacion(leida);

-- ------------------------------------------------------------
-- SESION (para token blacklist / control de logout)
-- ------------------------------------------------------------
CREATE TABLE sesion (
  id_sesion   INT AUTO_INCREMENT PRIMARY KEY,
  id_usuario  INT NOT NULL,
  token_jti   VARCHAR(36) NOT NULL UNIQUE,  -- JWT jti claim
  activa      BOOLEAN NOT NULL DEFAULT TRUE,
  created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  expires_at  DATETIME NOT NULL,
  CONSTRAINT fk_sesion_usuario FOREIGN KEY (id_usuario) REFERENCES usuario(id_usuario) ON DELETE CASCADE
);

CREATE INDEX idx_sesion_token_jti ON sesion(token_jti);
CREATE INDEX idx_sesion_usuario   ON sesion(id_usuario);