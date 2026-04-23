// ============================================================
// GuardianWater — Esquema MongoDB (NoSQL)
// Se usa para almacenar datos de alta escritura:
//   · Lecturas de sensores en tiempo real
//   · Logs de actividad
//   · Imágenes/documentos de reportes
//   · Caché de estadísticas por zona
// ============================================================

// ── BASE DE DATOS ────────────────────────────────────────────
use("guardianwater_nosql");


// ============================================================
// COLECCIÓN: sensor_readings
// Lecturas de sensores IoT de calidad de agua por zona.
// Alto volumen de escritura → MongoDB ideal.
// ============================================================
db.createCollection("sensor_readings", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["zona_id", "timestamp", "parametros"],
      properties: {
        zona_id: {
          bsonType: "int",
          description: "ID de la zona (referencia a MySQL zona.id_zona)"
        },
        dispositivo_id: {
          bsonType: "string",
          description: "Identificador único del sensor"
        },
        timestamp: {
          bsonType: "date",
          description: "Fecha y hora de la lectura"
        },
        parametros: {
          bsonType: "object",
          description: "Mediciones del sensor",
          properties: {
            ph:             { bsonType: "double", minimum: 0, maximum: 14 },
            turbidez_ntu:   { bsonType: "double", minimum: 0 },
            temperatura_c:  { bsonType: "double" },
            conductividad:  { bsonType: "double", minimum: 0 },
            cloro_libre:    { bsonType: "double", minimum: 0 },
            coliformes:     { bsonType: "double", minimum: 0 }
          }
        },
        calidad_calculada: {
          bsonType: "int",
          minimum: 1,
          maximum: 5,
          description: "Score calculado 1-5 basado en parámetros"
        },
        alerta: {
          bsonType: "bool",
          description: "True si algún parámetro está fuera de rango"
        },
        parametros_fuera_rango: {
          bsonType: "array",
          description: "Lista de parámetros que superaron límites",
          items: { bsonType: "string" }
        }
      }
    }
  }
});

// Índices para sensor_readings
db.sensor_readings.createIndex({ zona_id: 1, timestamp: -1 });
db.sensor_readings.createIndex({ timestamp: -1 });
db.sensor_readings.createIndex({ alerta: 1, timestamp: -1 });
db.sensor_readings.createIndex({ dispositivo_id: 1, timestamp: -1 });

// TTL: conservar lecturas por 1 año (365 días)
db.sensor_readings.createIndex(
  { timestamp: 1 },
  { expireAfterSeconds: 31536000 }
);

// Documento de ejemplo
db.sensor_readings.insertOne({
  zona_id: 1,
  dispositivo_id: "sensor-zona1-001",
  timestamp: new Date(),
  parametros: {
    ph: 7.2,
    turbidez_ntu: 1.5,
    temperatura_c: 18.5,
    conductividad: 350.0,
    cloro_libre: 0.5,
    coliformes: 0.0
  },
  calidad_calculada: 5,
  alerta: false,
  parametros_fuera_rango: []
});


// ============================================================
// COLECCIÓN: activity_logs
// Log de auditoría: acciones de usuarios en el sistema.
// Append-only → MongoDB ideal.
// ============================================================
db.createCollection("activity_logs", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["usuario_id", "accion", "timestamp"],
      properties: {
        usuario_id:   { bsonType: "int" },
        email:        { bsonType: "string" },
        accion:       { bsonType: "string" },
        recurso:      { bsonType: "string" },
        recurso_id:   { bsonType: ["int", "null"] },
        ip:           { bsonType: "string" },
        user_agent:   { bsonType: "string" },
        status_code:  { bsonType: "int" },
        timestamp:    { bsonType: "date" },
        detalle:      { bsonType: "object" }
      }
    }
  }
});

db.activity_logs.createIndex({ usuario_id: 1, timestamp: -1 });
db.activity_logs.createIndex({ accion: 1, timestamp: -1 });
db.activity_logs.createIndex({ timestamp: -1 });

// TTL: conservar logs 6 meses
db.activity_logs.createIndex(
  { timestamp: 1 },
  { expireAfterSeconds: 15552000 }
);


// ============================================================
// COLECCIÓN: reporte_media
// Metadatos de imágenes y archivos adjuntos a reportes.
// Evita guardar blobs en MySQL.
// ============================================================
db.createCollection("reporte_media", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["reporte_id", "url", "tipo_mime", "uploaded_at"],
      properties: {
        reporte_id:   { bsonType: "int",    description: "FK a MySQL reporte.id_reporte" },
        usuario_id:   { bsonType: "int" },
        url:          { bsonType: "string" },
        tipo_mime:    { bsonType: "string" },
        tamanio_kb:   { bsonType: "double" },
        ancho_px:     { bsonType: "int" },
        alto_px:      { bsonType: "int" },
        uploaded_at:  { bsonType: "date" }
      }
    }
  }
});

db.reporte_media.createIndex({ reporte_id: 1 });
db.reporte_media.createIndex({ usuario_id: 1 });


// ============================================================
// COLECCIÓN: zona_stats
// Estadísticas precalculadas por zona (para el dashboard admin).
// Se actualiza periódicamente con un job de agregación.
// ============================================================
db.createCollection("zona_stats");

db.zona_stats.createIndex({ zona_id: 1 }, { unique: true });
db.zona_stats.createIndex({ "ultima_actualizacion": -1 });

// Documento de ejemplo
db.zona_stats.insertOne({
  zona_id: 1,
  nombre_zona: "Centro Huauchinango",
  ultima_actualizacion: new Date(),
  total_reportes: 47,
  reportes_por_estado: {
    pendiente: 12,
    en_revision: 5,
    resuelto: 28,
    rechazado: 2
  },
  reportes_por_tipo: {
    problema: 30,
    comentario: 10,
    desconocido: 7
  },
  calidad_promedio_7d: 3.8,
  ultima_lectura_sensor: {
    timestamp: new Date(),
    ph: 7.1,
    turbidez_ntu: 1.8,
    calidad_calculada: 4,
    alerta: false
  }
});


// ============================================================
// COLECCIÓN: push_tokens
// Tokens FCM/APNs para notificaciones push (futuro móvil).
// ============================================================
db.createCollection("push_tokens");
db.push_tokens.createIndex({ usuario_id: 1 });
db.push_tokens.createIndex({ token: 1 }, { unique: true });

// Documento de ejemplo
db.push_tokens.insertOne({
  usuario_id: 5,
  token: "FCM_EXAMPLE_TOKEN_XXXX",
  plataforma: "android",
  activo: true,
  updated_at: new Date()
});