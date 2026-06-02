-- ============================================================
-- ESQUEMA MySQL: Sesión de Pair Programming
-- Historia de Usuario: Revisión colaborativa de tareas
-- ============================================================

CREATE DATABASE IF NOT EXISTS pair_programming_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE pair_programming_db;

-- Tabla de tareas revisadas
CREATE TABLE IF NOT EXISTS tareas (
    id VARCHAR(50) PRIMARY KEY,
    titulo VARCHAR(200) NOT NULL,
    descripcion TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de sesiones de pair programming
CREATE TABLE IF NOT EXISTS sesiones (
    id INT AUTO_INCREMENT PRIMARY KEY,
    task_id VARCHAR(50) NOT NULL,
    iniciada_en DATETIME DEFAULT CURRENT_TIMESTAMP,
    cerrada_en DATETIME NULL,
    activa BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (task_id) REFERENCES tareas(id)
);

-- Tabla de participantes por sesión
CREATE TABLE IF NOT EXISTS participantes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sesion_id INT NOT NULL,
    usuario VARCHAR(100) NOT NULL,
    estado ENUM('online', 'offline') DEFAULT 'online',
    conectado_en DATETIME DEFAULT CURRENT_TIMESTAMP,
    desconectado_en DATETIME NULL,
    FOREIGN KEY (sesion_id) REFERENCES sesiones(id)
);

-- Tabla de archivos abiertos por participante
CREATE TABLE IF NOT EXISTS archivos_abiertos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sesion_id INT NOT NULL,
    usuario VARCHAR(100) NOT NULL,
    nombre_archivo VARCHAR(300) NOT NULL,
    abierto_en DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sesion_id) REFERENCES sesiones(id)
);

-- Tabla de comentarios (CS3, CS4, CS6, CS8)
CREATE TABLE IF NOT EXISTS comentarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sesion_id INT NOT NULL,
    task_id VARCHAR(50) NOT NULL,
    usuario VARCHAR(100) NOT NULL,
    texto TEXT NOT NULL,
    compartido BOOLEAN DEFAULT FALSE,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sesion_id) REFERENCES sesiones(id),
    FOREIGN KEY (task_id) REFERENCES tareas(id)
);

-- Tabla de interacciones / historial completo (CS6, CS8)
CREATE TABLE IF NOT EXISTS interacciones (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sesion_id INT NOT NULL,
    task_id VARCHAR(50) NOT NULL,
    usuario VARCHAR(100) NOT NULL,
    accion VARCHAR(100) NOT NULL,
    detalle TEXT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sesion_id) REFERENCES sesiones(id)
);

-- Datos iniciales de ejemplo
INSERT IGNORE INTO tareas (id, titulo, descripcion) VALUES
('TASK-101', 'Revisión del módulo de autenticación', 'Revisar auth_service.py y validar el manejo de errores, try/except y helpers'),
('TASK-102', 'Refactorización del controlador de usuarios', 'Optimizar controllers.py para reducir complejidad ciclomática');
