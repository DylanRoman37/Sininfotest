from flask import Flask, jsonify, request
from flask_cors import CORS
from test_userstorie1 import ExtensionPairProgramming
from datetime import datetime
import mysql.connector

app = Flask(__name__)
CORS(app) 

sistema = ExtensionPairProgramming()

# ========================================================
# CONEXIÓN A TU BASE DE DATOS MYSQL
# ========================================================
def conectar_bd():
    return mysql.connector.connect(
        host="localhost",       # Cambia si usas Aiven u otro host
        user="root",            # Tu usuario de MySQL
        password="",            # Tu contraseña de MySQL (vacío por defecto en XAMPP)
        database="pair_programming_db"
    )

# Simulamos que estamos en la sesión 1 para este laboratorio
SESION_ACTUAL_ID = 1 

@app.route('/api/conectar', methods=['POST'])
def conectar():
    data = request.json
    usuario = data['usuario']
    
    # 1. El backend (TDD) verifica si puede entrar
    exito = sistema.intentar_ingreso(usuario)
    
    # 2. Si entró con éxito, lo guardamos en tu tabla 'participantes'
    if exito:
        sistema.registrar_evento(usuario, "Conectado", datetime.now().strftime("%H:%M:%S"))
        
        try:
            bd = conectar_bd()
            cursor = bd.cursor()
            # Insertamos al participante en MySQL
            query = """
                INSERT INTO participantes (sesion_id, usuario, estado, conectado_en) 
                VALUES (%s, %s, 'online', NOW())
            """
            cursor.execute(query, (SESION_ACTUAL_ID, usuario))
            bd.commit()
            cursor.close()
            bd.close()
        except Exception as e:
            print("Error guardando en BD:", e)
            
    return jsonify({"exito": exito})

@app.route('/api/desconectar', methods=['POST'])
def desconectar():
    usuario = request.json['usuario']
    
    # 1. El backend lo desconecta de la memoria
    sistema.desconectar_usuario(usuario)
    sistema.registrar_evento(usuario, "Desconectado", datetime.now().strftime("%H:%M:%S"))
    
    # 2. Actualizamos el estado en tu BD a 'offline' y ponemos la hora
    try:
        bd = conectar_bd()
        cursor = bd.cursor()
        query = """
            UPDATE participantes 
            SET estado = 'offline', desconectado_en = NOW() 
            WHERE sesion_id = %s AND usuario = %s AND estado = 'online'
        """
        cursor.execute(query, (SESION_ACTUAL_ID, usuario))
        bd.commit()
        cursor.close()
        bd.close()
    except Exception as e:
        print("Error actualizando en BD:", e)
        
    return jsonify({"exito": True})

@app.route('/api/archivo', methods=['POST'])
def cambiar_archivo():
    data = request.json
    sistema.abrir_archivo(data['usuario'], data['archivo'])
    sincronizados = sistema.verificar_sincronizacion()
    return jsonify({"exito": True, "sincronizados": sincronizados})

if __name__ == '__main__':
    print("🚀 Servidor Backend corriendo en http://localhost:5000")
    app.run(debug=True)