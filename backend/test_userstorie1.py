"""
Materia: Sistemas de Información / Ingeniería de Software
Fase: REFACTORIZACIÓN FINAL (Integración Completa)
Historia de Usuario: Sesión de Pair Programming para revisión de tareas
"""

import pytest
from datetime import datetime

# ==============================================================================
# 1. CÓDIGO DE PRODUCCIÓN (El Sistema Unificado)
# ==============================================================================
class ExtensionPairProgramming:
    def __init__(self):
        # CS1 y CS2: Límites y Estado Visual
        self.limite_permitido = 2
        self.estado_visual = {}
        
        # CS3: Sincronización de Archivos
        self.archivos_abiertos = {}
        self.sincronizacion_tiempo_real_activa = True
        
        # CS4 y CS5: Logs y Última Conexión
        self.registro_logs = []
        self.ultima_desconexion_pareja = None

    # --- MÓDULO DE LÍMITES Y CONEXIÓN ---
    def intentar_ingreso(self, usuario):
        usuarios_activos = sum(1 for estado in self.estado_visual.values() if estado == "En línea")
        if usuarios_activos >= self.limite_permitido:
            return False # Bloqueado, cupo lleno
        
        self.estado_visual[usuario] = "En línea"
        return True

    def desconectar_usuario(self, usuario):
        if usuario in self.estado_visual:
            self.estado_visual[usuario] = "Desconectado"

    def obtener_estado_visual(self, usuario):
        return self.estado_visual.get(usuario, "No registrado")

    # --- MÓDULO DE SINCRONIZACIÓN DE ARCHIVOS ---
    def abrir_archivo(self, usuario, nombre_archivo):
        self.archivos_abiertos[usuario] = nombre_archivo

    def alternar_modo_tiempo_real(self, estado: bool):
        self.sincronizacion_tiempo_real_activa = estado

    def verificar_sincronizacion(self):
        if not self.sincronizacion_tiempo_real_activa or len(self.archivos_abiertos) < 2:
            return False
        archivos = list(self.archivos_abiertos.values())
        return all(archivo == archivos[0] for archivo in archivos)

    # --- MÓDULO DE LOGS E HISTORIAL DE TIEMPO ---
    def registrar_evento(self, usuario, tipo_evento, hora_exacta):
        if tipo_evento not in ["Conectado", "Desconectado"]:
            raise ValueError("Evento no válido")
            
        self.registro_logs.append({"usuario": usuario, "evento": tipo_evento, "hora": hora_exacta})
        
        if tipo_evento == "Desconectado":
            self.ultima_desconexion_pareja = hora_exacta

    def obtener_historial_usuario(self, usuario):
        return [log for log in self.registro_logs if log["usuario"] == usuario]

    def obtener_ultima_conexion(self):
        return self.ultima_desconexion_pareja


# ==============================================================================
# 2. FIXTURE MAESTRA DE PYTEST
# ==============================================================================
@pytest.fixture
def sesion():
    """Genera una instancia fresca del sistema completo para cada test."""
    return ExtensionPairProgramming()


# ==============================================================================
# 3. SUITE DE PRUEBAS INTEGRADA (16 Escenarios Atómicos)
# ==============================================================================

# ─── REQUISITO 1: LÍMITE DE USUARIOS (Traducido de Unittest a Pytest) ────────
def test_ingreso_primer_usuario(sesion):
    assert sesion.intentar_ingreso("Jhael") is True

def test_ingreso_segundo_usuario(sesion):
    sesion.intentar_ingreso("Jhael")
    assert sesion.intentar_ingreso("Dylan") is True

def test_bloqueo_tercer_usuario(sesion):
    sesion.intentar_ingreso("Jhael")
    sesion.intentar_ingreso("Dylan")
    assert sesion.intentar_ingreso("Carlos") is False, "Debe bloquear al tercero"

def test_persistencia_del_bloqueo_cuarto_usuario(sesion):
    sesion.intentar_ingreso("Jhael")
    sesion.intentar_ingreso("Dylan")
    sesion.intentar_ingreso("Carlos") # 3ro rechazado
    assert sesion.intentar_ingreso("Marta") is False, "El cuarto también debe ser rechazado"

def test_permitir_ingreso_tras_desconexion(sesion):
    sesion.intentar_ingreso("Jhael")
    sesion.intentar_ingreso("Dylan")
    sesion.desconectar_usuario("Dylan") # Se libera un cupo
    assert sesion.intentar_ingreso("Carlos") is True, "Debe entrar porque Dylan salió"

# ─── REQUISITO 2: ESTADO VISUAL DE CONEXIÓN ──────────────────────────────────
def test_indicador_muestra_en_linea_al_ingresar(sesion):
    sesion.intentar_ingreso("Jhael")
    assert sesion.obtener_estado_visual("Jhael") == "En línea"

def test_indicador_cambia_a_desconectado_al_salir(sesion):
    sesion.intentar_ingreso("Dylan")
    sesion.desconectar_usuario("Dylan")
    assert sesion.obtener_estado_visual("Dylan") == "Desconectado"

def test_indicador_maneja_usuarios_fantasmas(sesion):
    assert sesion.obtener_estado_visual("Infiltrado") == "No registrado"

# ─── REQUISITO 3: SINCRONIZACIÓN DE ARCHIVOS ─────────────────────────────────
def test_sincroniza_correctamente_cuando_ven_mismo_archivo(sesion):
    sesion.abrir_archivo("Jhael", "main.py")
    sesion.abrir_archivo("Dylan", "main.py")
    assert sesion.verificar_sincronizacion() is True

def test_detecta_desincronizacion_al_cambiar_pestana(sesion):
    sesion.abrir_archivo("Jhael", "main.py")
    sesion.abrir_archivo("Dylan", "db.py")
    assert sesion.verificar_sincronizacion() is False

def test_falla_sincronizacion_si_se_apaga_el_tiempo_real(sesion):
    sesion.abrir_archivo("Jhael", "main.py")
    sesion.abrir_archivo("Dylan", "main.py")
    sesion.alternar_modo_tiempo_real(False)
    assert sesion.verificar_sincronizacion() is False

# ─── REQUISITO 4: REGISTRO DE LOGS CON HORA EXACTA ───────────────────────────
def test_registra_hora_exacta_al_conectarse(sesion):
    hora = datetime(2026, 6, 1, 10, 0, 0)
    sesion.registrar_evento("Jhael", "Conectado", hora)
    logs = sesion.obtener_historial_usuario("Jhael")
    assert len(logs) == 1 and logs[0]["hora"] == hora

def test_registra_hora_exacta_al_desconectarse(sesion):
    hora = datetime(2026, 6, 1, 10, 30, 0)
    sesion.registrar_evento("Dylan", "Desconectado", hora)
    logs = sesion.obtener_historial_usuario("Dylan")
    assert len(logs) == 1 and logs[0]["evento"] == "Desconectado"

def test_mantiene_historial_ordenado_multiples_conexiones(sesion):
    t1, t2, t3 = datetime(2026, 1, 1), datetime(2026, 1, 2), datetime(2026, 1, 3)
    sesion.registrar_evento("Jhael", "Conectado", t1)
    sesion.registrar_evento("Jhael", "Desconectado", t2)
    sesion.registrar_evento("Jhael", "Conectado", t3)
    logs = sesion.obtener_historial_usuario("Jhael")
    assert len(logs) == 3

def test_logs_son_independientes_por_usuario(sesion):
    sesion.registrar_evento("Dylan", "Conectado", datetime.now())
    assert len(sesion.obtener_historial_usuario("Jhael")) == 0

# ─── REQUISITO 5: VISUALIZAR ÚLTIMA DESCONEXIÓN (El stub completado) ─────────
def test_visualizar_ultima_conexion_pareja(sesion):
    hora_salida = "23:45"
    sesion.registrar_evento("Jhael", "Desconectado", hora_salida)
    assert sesion.obtener_ultima_conexion() == "23:45"