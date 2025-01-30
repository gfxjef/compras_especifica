import os
import mysql.connector
from flask import Flask, jsonify, request
from datetime import datetime
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Configuración de la base de datos
DB_CONFIG = {
    'user': os.environ.get('MYSQL_USER'),
    'password': os.environ.get('MYSQL_PASSWORD'),
    'host': os.environ.get('MYSQL_HOST'),
    'database': os.environ.get('MYSQL_DATABASE'),
    'port': int(os.environ.get('MYSQL_PORT', 3306)),
    'ssl_ca': os.environ.get('MYSQL_SSL_CA') or None
}

def get_db_connection():
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except mysql.connector.Error as err:
        raise RuntimeError(f"Error de conexión MySQL: {err}")

# Validaciones
def validar_datos_compra(data):
    requeridos = ['sku', 'boleta_factura', 'unidades']
    for campo in requeridos:
        if not data.get(campo):
            raise ValueError(f'Campo requerido: {campo}')
    
    if int(data.get('unidades', 0)) <= 0:
        raise ValueError('Unidades debe ser mayor a 0')

# Crear registro
@app.route('/crear', methods=['POST'])
def crear_registro():
    try:
        data = request.get_json()
        validar_datos_compra(data)
        
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        query = """
            INSERT INTO comp_especifica (
                timestamp, sku, boleta_factura, marca, modelo,
                tamano, categoria, tipo_compra, bonificacion,
                unidades, monto, costo_unitario
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        values = (
            datetime.now(),
            data['sku'],
            data['boleta_factura'],
            data.get('marca', ''),
            data.get('modelo', ''),
            data.get('tamano', ''),
            data.get('categoria', ''),
            data.get('tipo_compra', ''),
            bool(data.get('bonificacion', False)),
            int(data['unidades']),
            float(data.get('monto', 0)),
            float(data.get('costo_unitario', 0))
        )

        cursor.execute(query, values)
        connection.commit()
        
        cursor.close()
        connection.close()

        return jsonify({
            'success': True,
            'message': 'Registro creado exitosamente'
        }), 201

    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Editar registro
@app.route('/editar/<int:id>', methods=['PUT'])
def editar_registro(id):
    try:
        data = request.get_json()
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        campos_permitidos = [
            'sku', 'boleta_factura', 'marca', 'modelo',
            'tamano', 'categoria', 'tipo_compra',
            'bonificacion', 'unidades', 'monto', 'costo_unitario'
        ]
        
        updates = []
        values = []
        for campo in campos_permitidos:
            if campo in data:
                updates.append(f"{campo} = %s")
                values.append(data[campo])

        if not updates:
            return jsonify({'success': False, 'error': 'No hay datos para actualizar'}), 400

        query = f"UPDATE comp_especifica SET {', '.join(updates)} WHERE id = %s"
        values.append(id)
        
        cursor.execute(query, values)
        connection.commit()
        cursor.close()
        connection.close()

        return jsonify({
            'success': True,
            'message': 'Registro actualizado'
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Consultar registros
@app.route('/consultar', methods=['GET'])
def consultar_registros():
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        
        cursor.execute("SELECT * FROM comp_especifica")
        registros = cursor.fetchall()
        
        cursor.close()
        connection.close()
        
        return jsonify({
            'success': True,
            'data': registros,
            'count': len(registros)
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', 
            port=os.environ.get('PORT', 5000),
            debug=os.environ.get('FLASK_DEBUG', 'False') == 'True')