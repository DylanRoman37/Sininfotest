

from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import mysql.connector
import os

app = Flask(__name__)
CORS(app)

# ============================================================
# CONFIGURACIÓN DE BASE DE DATOS
# ============================================================

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", "1234"),
    "database": os.getenv("DB_NAME", "pair_programming_db"),
    "charset": "utf8mb4",
    "autocommit": True,
}

def get_db():
    """Obtiene una conexión a MySQL."""
    return mysql.connector.connect(**DB_CONFIG)


# ============================================================
# CÓDIGO DE PRODUCCIÓN: SesionPairProgramming (misma lógica de los tests)
# ============================================================

class SesionPairProgramming:
    def __init__(self, task_id):
        self.task_id = task_id
        self.limite_usuarios = 2

        # CS1 y CS7: Estado de conexión de los participantes
        self.participantes = {}

        # CS2: Control de archivos abiertos en tiempo real
        self.archivos_abiertos = {}
        self.realtime_sync_active = True

        # CS3 y CS4: Gestión de comentarios
        self.comments = []
        self.shared_comments = []
        self.shared_comments_section_enabled = True

        # CS5: Sincronización automática
        self.auto_sync_enabled = True
        self.last_sync_status = "success"

        # CS6: Historial de interacciones
        self.interactions = []

        # CS8: Persistencia del historial
        self.history_saved = False
        self.history_linked_to_task = None

    def conectar_usuario(self, usuario):
        # CORRECCIÓN: Contamos SOLO los participantes que están realmente "online"
        usuarios_activos = sum(1 for estado in self.participantes.values() if estado == "online")
        
        # Si ya se alcanzó el límite y el usuario que intenta entrar NO está online actualmente, bloquear
        if usuarios_activos >= self.limite_usuarios and self.participantes.get(usuario) != "online":
            return False
            
        self.participantes[usuario] = "online"
        return True
    
    def desconectar_usuario(self, usuario):
        if usuario in self.participantes:
            self.participantes[usuario] = "offline"

        if usuario in self.archivos_abiertos:
            del self.archivos_abiertos[usuario]

    def abrir_archivo(self, usuario, nombre_archivo):
        self.archivos_abiertos[usuario] = nombre_archivo.strip().lower()

    def verificar_sincronizacion_archivo(self):
        if not self.realtime_sync_active:
            return False

        usuarios_online = [
            usuario
            for usuario, estado in self.participantes.items()
            if estado == "online"
        ]

        if len(usuarios_online) < 2:
            return False

        archivos = []

        for usuario in usuarios_online:
            archivo = self.archivos_abiertos.get(usuario)

            if not archivo:
                return False

            archivos.append(archivo)

        return len(set(archivos)) == 1

    def agregar_comentario(self, usuario, texto, compartido=False):
        comentario = {"user": usuario, "text": texto}
        if compartido:
            self.shared_comments.append(comentario)
        else:
            self.comments.append(comentario)

        self.interactions.append({
            "user": usuario,
            "action": "comment_shared" if compartido else "comment",
            "timestamp": datetime.now()
        })

    def guardar_historial_tarea(self):
        if self.task_id:
            self.history_saved = True
            self.history_linked_to_task = self.task_id
            return True
        return False


# ============================================================
# ESTADO EN MEMORIA (simple session store — en producción usar Redis)
# ============================================================

sesiones_activas: dict[str, SesionPairProgramming] = {}


def obtener_o_crear_sesion(task_id: str) -> SesionPairProgramming:
    if task_id not in sesiones_activas:
        sesiones_activas[task_id] = SesionPairProgramming(task_id)
    return sesiones_activas[task_id]


# ============================================================
# ENDPOINTS
# ============================================================

# ── Tareas disponibles ──────────────────────────────────────

@app.route("/api/tareas", methods=["GET"])
def listar_tareas():
    """Devuelve las tareas disponibles para revisar."""
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM tareas ORDER BY created_at DESC")
    tareas = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(tareas)


# ── CS1 & CS7: Conexión de participantes ────────────────────

@app.route("/api/sesion/<task_id>/conectar", methods=["POST"])
def conectar_usuario(task_id):
    """CS1: Permite el acceso simultáneo (máx. 2 devs). CS7: Marca estado online."""
    data = request.json
    usuario = data.get("usuario", "").strip()
    if not usuario:
        return jsonify({"error": "Nombre de usuario requerido"}), 400

    sesion = obtener_o_crear_sesion(task_id)
    resultado = sesion.conectar_usuario(usuario)

    if not resultado:
        return jsonify({
            "success": False,
            "message": f"Límite de {sesion.limite_usuarios} desarrolladores alcanzado. Pair programming requiere exactamente 2 devs."
        }), 409

    # Persistir en MySQL
    conn = get_db()
    cur = conn.cursor()

    # Buscar o crear sesión en BD
    cur.execute("SELECT id FROM sesiones WHERE task_id = %s AND activa = TRUE", (task_id,))
    row = cur.fetchone()
    if not row:
        cur.execute(
            "INSERT INTO sesiones (task_id) VALUES (%s)",
            (task_id,)
        )
        sesion_id = cur.lastrowid
    else:
        sesion_id = row[0]

    cur.execute(
        "INSERT INTO participantes (sesion_id, usuario, estado) VALUES (%s, %s, 'online')",
        (sesion_id, usuario)
    )
    cur.execute(
        "INSERT INTO interacciones (sesion_id, task_id, usuario, accion, detalle) VALUES (%s, %s, %s, %s, %s)",
        (sesion_id, task_id, usuario, "conectado", f"{usuario} se unió a la sesión")
    )
    cur.close()
    conn.close()

    return jsonify({
        "success": True,
        "message": f"{usuario} conectado exitosamente",
        "participantes": sesion.participantes,
        "auto_sync_enabled": sesion.auto_sync_enabled,
        "shared_comments_section_enabled": sesion.shared_comments_section_enabled,
    })


@app.route("/api/sesion/<task_id>/desconectar", methods=["POST"])
def desconectar_usuario(task_id):
    """CS7: Cambia estado a offline cuando el dev abandona la sesión."""
    data = request.json
    usuario = data.get("usuario", "").strip()

    sesion = obtener_o_crear_sesion(task_id)
    sesion.desconectar_usuario(usuario)
    sesion.guardar_historial_tarea()  # CS8: Guardar historial al cerrar

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT id FROM sesiones WHERE task_id = %s AND activa = TRUE", (task_id,)
    )
    row = cur.fetchone()
    if row:
        sesion_id = row[0]
        cur.execute(
            "UPDATE participantes SET estado='offline', desconectado_en=NOW() WHERE sesion_id=%s AND usuario=%s",
            (sesion_id, usuario)
        )
        cur.execute(
            "INSERT INTO interacciones (sesion_id, task_id, usuario, accion, detalle) VALUES (%s, %s, %s, %s, %s)",
            (sesion_id, task_id, usuario, "desconectado", f"{usuario} salió de la sesión")
        )
    cur.close()
    conn.close()

    return jsonify({
        "success": True,
        "history_saved": sesion.history_saved,
        "history_linked_to_task": sesion.history_linked_to_task,
        "participantes": sesion.participantes,
    })


# ── CS2: Sincronización de archivos ─────────────────────────

@app.route("/api/sesion/<task_id>/abrir-archivo", methods=["POST"])
def abrir_archivo(task_id):
    """CS2: Registra qué archivo está viendo cada dev y valida sincronización."""
    data = request.json
    usuario = data.get("usuario", "").strip()
    nombre_archivo = data.get("archivo", "").strip().lower()

    sesion = obtener_o_crear_sesion(task_id)
    sesion.abrir_archivo(usuario, nombre_archivo)
    sincronizado = sesion.verificar_sincronizacion_archivo()

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id FROM sesiones WHERE task_id = %s AND activa = TRUE", (task_id,))
    row = cur.fetchone()
    if row:
        sesion_id = row[0]
        cur.execute(
            "INSERT INTO archivos_abiertos (sesion_id, usuario, nombre_archivo) VALUES (%s, %s, %s)",
            (sesion_id, usuario, nombre_archivo)
        )
        cur.execute(
            "INSERT INTO interacciones (sesion_id, task_id, usuario, accion, detalle) VALUES (%s, %s, %s, %s, %s)",
            (sesion_id, task_id, usuario, "abrir_archivo", nombre_archivo)
        )
    cur.close()
    conn.close()

    return jsonify({
        "success": True,
        "archivos_abiertos": sesion.archivos_abiertos,
        "sincronizado": sincronizado,
        "sync_status": "✅ Sincronizados — Mismo archivo" if sincronizado else "⚠️ Desincronizados — Archivos distintos",
    })


# ── CS3 & CS4 & CS6: Comentarios ────────────────────────────

@app.route("/api/sesion/<task_id>/comentar", methods=["POST"])
def agregar_comentario(task_id):
    """CS3: Identifica autor. CS4: Sección compartida. CS6: Timestamp automático."""
    data = request.json
    usuario = data.get("usuario", "").strip()
    texto = data.get("texto", "").strip()
    compartido = data.get("compartido", False)

    if not usuario or not texto:
        return jsonify({"error": "Usuario y texto son requeridos"}), 400

    sesion = obtener_o_crear_sesion(task_id)
    sesion.agregar_comentario(usuario, texto, compartido)

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id FROM sesiones WHERE task_id = %s AND activa = TRUE", (task_id,))
    row = cur.fetchone()
    sesion_id = None
    if row:
        sesion_id = row[0]
        cur.execute(
            """INSERT INTO comentarios (sesion_id, task_id, usuario, texto, compartido)
               VALUES (%s, %s, %s, %s, %s)""",
            (sesion_id, task_id, usuario, texto, compartido)
        )
        cur.execute(
            "INSERT INTO interacciones (sesion_id, task_id, usuario, accion, detalle) VALUES (%s, %s, %s, %s, %s)",
            (sesion_id, task_id, usuario, "comment_shared" if compartido else "comment", texto[:100])
        )
    cur.close()
    conn.close()

    return jsonify({
        "success": True,
        "comentario": {
            "user": usuario,
            "text": texto,
            "compartido": compartido,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        },
        "total_comments": len(sesion.comments),
        "total_shared": len(sesion.shared_comments),
    })


@app.route("/api/sesion/<task_id>/comentarios", methods=["GET"])
def obtener_comentarios(task_id):
    """Devuelve todos los comentarios de la sesión desde MySQL (CS3, CS4, CS6, CS8)."""
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute(
        """SELECT c.usuario, c.texto, c.compartido, c.timestamp
           FROM comentarios c
           JOIN sesiones s ON c.sesion_id = s.id
           WHERE c.task_id = %s
           ORDER BY c.timestamp ASC""",
        (task_id,)
    )
    comentarios = cur.fetchall()
    for c in comentarios:
        c["timestamp"] = c["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
        c["compartido"] = bool(c["compartido"])
    cur.close()
    conn.close()
    return jsonify(comentarios)


# ── CS5: Estado de sincronización ───────────────────────────

@app.route("/api/sesion/<task_id>/estado", methods=["GET"])
def estado_sesion(task_id):
    """CS5: Valida que la sincronización automática esté activa y muestra el estado completo."""
    sesion = obtener_o_crear_sesion(task_id)

    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute(
        """SELECT usuario, estado, conectado_en, desconectado_en
           FROM participantes p
           JOIN sesiones s ON p.sesion_id = s.id
           WHERE s.task_id = %s AND s.activa = TRUE
           ORDER BY p.conectado_en DESC""",
        (task_id,)
    )
    participantes_db = cur.fetchall()
    for p in participantes_db:
        if p["conectado_en"]:
            p["conectado_en"] = p["conectado_en"].strftime("%Y-%m-%d %H:%M:%S")
        if p["desconectado_en"]:
            p["desconectado_en"] = p["desconectado_en"].strftime("%Y-%m-%d %H:%M:%S")

    cur.execute(
        """SELECT usuario, nombre_archivo, abierto_en
           FROM archivos_abiertos a
           JOIN sesiones s ON a.sesion_id = s.id
           WHERE s.task_id = %s AND s.activa = TRUE
           ORDER BY a.abierto_en DESC""",
        (task_id,)
    )
    archivos_db = cur.fetchall()
    for a in archivos_db:
        a["abierto_en"] = a["abierto_en"].strftime("%Y-%m-%d %H:%M:%S")

    cur.close()
    conn.close()

    return jsonify({
        "task_id": task_id,
        "auto_sync_enabled": sesion.auto_sync_enabled,        # CS5
        "last_sync_status": sesion.last_sync_status,           # CS5
        "shared_comments_section_enabled": sesion.shared_comments_section_enabled,  # CS4
        "realtime_sync_active": sesion.realtime_sync_active,   # CS2
        "participantes_memoria": sesion.participantes,          # CS7
        "participantes_db": participantes_db,                   # CS7
        "archivos_abiertos": sesion.archivos_abiertos,         # CS2
        "archivos_db": archivos_db,
        "sincronizado": sesion.verificar_sincronizacion_archivo(),  # CS2
        "history_saved": sesion.history_saved,                 # CS8
        "history_linked_to_task": sesion.history_linked_to_task,   # CS8
    })


# ── CS6 & CS8: Historial completo de interacciones ──────────

@app.route("/api/sesion/<task_id>/historial", methods=["GET"])
def historial_interacciones(task_id):
    """CS6 & CS8: Devuelve el historial completo vinculado a la tarea."""
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute(
        """SELECT i.usuario, i.accion, i.detalle, i.timestamp
           FROM interacciones i
           WHERE i.task_id = %s
           ORDER BY i.timestamp DESC
           LIMIT 100""",
        (task_id,)
    )
    historial = cur.fetchall()
    for h in historial:
        h["timestamp"] = h["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
    cur.close()
    conn.close()
    return jsonify(historial)


@app.route("/api/sesion/<task_id>/guardar-historial", methods=["POST"])
def guardar_historial(task_id):
    """CS8: Guarda y vincula el historial a la tarea."""
    sesion = obtener_o_crear_sesion(task_id)
    resultado = sesion.guardar_historial_tarea()
    return jsonify({
        "success": resultado,
        "history_saved": sesion.history_saved,
        "history_linked_to_task": sesion.history_linked_to_task,
    })


# ── Health check ─────────────────────────────────────────────

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
# ── ALIMENTANDO LOS TESTS CON UN QUERY (EL TUYO) ───────────
@app.route("/api/sesion/<task_id>/tests", methods=["GET"])
def obtener_tests(task_id):
    """Devuelve la lista de tests válidos para que el frontend los renderice"""
    return jsonify([
        {"id": "cs1", "desc": "CS1 · Impedir que un tercer usuario se una (Límite 2)"},
        {"id": "cs2", "desc": "CS2 · Indicador visual de conexión (En línea / Desconectado)"},
        {"id": "cs3", "desc": "CS3 · Visualizar el mismo archivo en tiempo real"},
        {"id": "cs4", "desc": "CS4 · Registro (log) con hora exacta de conexión/desconexión"},
        {"id": "cs5", "desc": "CS5 · Visualizar la última conexión de la pareja"}
    ])

# ── QUERY EXCLUSIVO PARA LA PANTALLA DE JHAEL ───────────
@app.route("/api/sesion/<task_id>/tests_jhael", methods=["GET"])
def obtener_tests_jhael(task_id):
    """Devuelve los 8 tests oficiales para el frontend de Jhael"""
    return jsonify([
        {"id": "cs1", "desc": "CS1 · 2 desarrolladores simultáneos"},
        {"id": "cs2", "desc": "CS2 · Visualizar mismo archivo en tiempo real"},
        {"id": "cs3", "desc": "CS3 · Mostrar autor de cada comentario"},
        {"id": "cs4", "desc": "CS4 · Sección compartida de comentarios"},
        {"id": "cs5", "desc": "CS5 · Sincronización automática de cambios"},
        {"id": "cs6", "desc": "CS6 · Registrar fecha y hora (Timestamp)"},
        {"id": "cs7", "desc": "CS7 · Mostrar estado de conexión"},
        {"id": "cs8", "desc": "CS8 · Historial guardado junto a la tarea"}
    ])

if __name__ == "__main__":
    print("🚀 Iniciando Servidor de Pair Programming...")
    app.run(debug=True, host="0.0.0.0", port=5000)
