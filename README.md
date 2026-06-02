# Pair Programming Session Hub
## Historia de Usuario: Sesión de Pair Programming para revisión de tareas

---

## Arquitectura

```
pair-programming/
├── index.html          # Menú principal (Jhael / Dylan)
├── jhael.html          # Interfaz completa de sesión
├── app.py              # Backend Flask (Python)
├── schema.sql          # Esquema MySQL
├── requirements.txt    # Dependencias Python
└── README.md
```

---

## Configuración paso a paso

### 1. Base de datos MySQL

```bash
# Entrar a MySQL
mysql -u root -p

# Ejecutar el schema
source schema.sql;
# o bien:
mysql -u root -p < schema.sql
```

### 2. Backend Python/Flask

```bash
# Crear entorno virtual
python -m venv venv
source venv/bin/activate       # Linux/Mac
venv\Scripts\activate          # Windows

# Instalar dependencias
pip install -r requirements.txt

# Variables de entorno (opcional si usas root sin contraseña)
export DB_HOST=localhost
export DB_USER=root
export DB_PASSWORD=tu_contraseña
export DB_NAME=pair_programming_db

# Ejecutar el servidor
python app.py
# → Corre en http://localhost:5000
```

### 3. Frontend

Abre `index.html` directamente en el navegador, o sirve con:

```bash
python -m http.server 8080
# → http://localhost:8080
```

---

## Cobertura de Condiciones de Satisfacción

| CS | Descripción | Implementado en |
|----|-------------|-----------------|
| CS1 | Máximo 2 devs simultáneos | `conectar_usuario()` + endpoint `/conectar` |
| CS2 | Mismo archivo en tiempo real | `verificar_sincronizacion_archivo()` + polling 4s |
| CS3 | Identificación de autor en comentarios | Campo `usuario` en cada comentario |
| CS4 | Sección compartida de comentarios | Toggle "Compartido" + tab separado |
| CS5 | Sincronización automática | `auto_sync_enabled=True` + polling |
| CS6 | Fecha y hora de cada interacción | `timestamp DATETIME` en MySQL + `datetime.now()` |
| CS7 | Estado de conexión (online/offline) | `participantes` dict + tabla `participantes` |
| CS8 | Historial vinculado a la tarea | `guardar_historial_tarea()` + tabla `interacciones` |

---

## Tests (pytest)

```bash
pytest test_sesion.py -v
```

Los tests son los mismos del archivo original, ahora respaldados por la implementación completa.
