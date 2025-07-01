import sqlite3
import os

DB_PATH = os.path.join("/data", "marcados.db")
def conectar():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def crear_tabla_si_no_existe():
    with conectar() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS marcados (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cedula TEXT,
                contrato TEXT,
                factura TEXT,
                estado TEXT CHECK(estado IN ('encontrado', 'no_encontrado')),
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        ''')

def marcar_fila(cedula, contrato, factura, estado):
    with conectar() as conn:
        conn.execute('''
            INSERT INTO marcados (cedula, contrato, factura, estado)
            VALUES (?, ?, ?, ?)
        ''', (cedula, contrato, factura, estado))

def obtener_estado(cedula, contrato, factura):
    with conectar() as conn:
        cursor = conn.execute('''
            SELECT estado FROM marcados
            WHERE cedula = ? AND contrato = ? AND factura = ?
            ORDER BY timestamp DESC LIMIT 1
        ''', (cedula, contrato, factura))
        row = cursor.fetchone()
        return row['estado'] if row else 'sin_marcar'
