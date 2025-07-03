# app.py

# Se añaden 'redirect' y 'url_for' a la lista de importaciones
from flask import Flask, render_template, request, Response, stream_with_context, redirect, url_for
import alfresco_service
from datetime import datetime
import openpyxl 
import os
import mimetypes
from PIL import Image
from io import BytesIO
from PyPDF2 import PdfReader
import sqlite3
from db_marcados import crear_tabla_si_no_existe, marcar_fila, obtener_estado
crear_tabla_si_no_existe()




app = Flask(__name__)

# --- CONFIGURACIÓN DE ARCHIVOS ---
# Ruta actualizada para apuntar a tu archivo Excel en la carpeta de Descargas
EXCEL_FILE_PATH = "SIC_FACTURAS_UNE_VERSION_FINAL.xlsx"
def detectar_tipo_mime(nombre):
    tipo, _ = mimetypes.guess_type(nombre)
    return tipo or 'application/octet-stream'

def es_pdf_valido(contenido_bytes):
    try:
        PdfReader(BytesIO(contenido_bytes))
        return True
    except Exception:
        return False

def convertir_tiff_a_png(tiff_bytes):
    try:
        imagen = Image.open(BytesIO(tiff_bytes))
        png_buffer = BytesIO()
        imagen.save(png_buffer, format="PNG")
        png_buffer.seek(0)
        return png_buffer
    except Exception:
        return None
    try:
        imagen = Image.open(BytesIO(tiff_bytes))
        png_buffer = BytesIO()
        imagen.save(png_buffer, format="PNG")
        png_buffer.seek(0)
        return png_buffer
    except Exception:
        return None

# Agrega la extensión .tif si el nombre no la tiene
def asegurar_extension(nombre, extension=".tif"):
    """Agrega una extensión si el nombre no la tiene."""
    if '.' not in nombre:
        return f"{nombre}{extension}"
    return nombre

#Función para detectar la extensión y devolver el Content-Type correcto
def detectar_tipo_mime(nombre):
    tipo, _ = mimetypes.guess_type(nombre)
    return tipo or 'application/octet-stream'

# --- Filtro de Jinja2 para formatear la fecha ---
@app.template_filter('format_date')
def format_date(iso_string):
    if not iso_string: return "N/A"
    try:
        # Maneja diferentes formatos de fecha que puedan venir del Excel o la API
        if isinstance(iso_string, datetime): return iso_string.strftime('%Y-%m-%d')
        if iso_string.endswith('+0000'): iso_string = iso_string.replace('+0000', '+00:00')
        dt_object = datetime.fromisoformat(iso_string)
        return dt_object.strftime('%Y-%m-%d %H:%M')
    except (ValueError, TypeError):
        return iso_string

# --- NUEVA FUNCIÓN PARA LEER EL EXCEL ---
def leer_excel():
    """Lee el archivo Excel y devuelve los datos como una lista de diccionarios."""
    filas = []
    if not os.path.exists(EXCEL_FILE_PATH):
        print(f"ERROR: No se encuentra el archivo Excel en la ruta: {EXCEL_FILE_PATH}")
        return None
        
    workbook = openpyxl.load_workbook(EXCEL_FILE_PATH)
    sheet = workbook.active
    
    # Asume que la primera fila es la cabecera
    headers = [cell.value for cell in sheet[1]]
    
    for row in sheet.iter_rows(min_row=2, values_only=True):
        fila_dict = dict(zip(headers, row))
        filas.append(fila_dict)
        
    return filas

# --- Rutas de la aplicación ---
@app.route('/')
def pagina_de_inicio():
    return render_template('index.html')

# --- RUTA DE BÚSQUEDA GENÉRICA (REACTIVADA) ---
@app.route('/search', methods=['POST'])
def manejar_busqueda():
    """
    Recibe los términos de la barra de búsqueda principal y busca en Alfresco.
    """
    termino_busqueda_raw = request.form.get('termino', '')
    # Dividimos por espacios para buscar cada palabra
    terminos = termino_busqueda_raw.split()

    if not terminos:
        return render_template('index.html', error="Por favor, introduce un término de búsqueda.")

    # Llamamos a la nueva función de búsqueda genérica en el servicio
    resultados = alfresco_service.buscar_archivos_generico(terminos)

    if resultados is None:
        return render_template('resultados.html', error="Error al conectar con el servidor de Alfresco.", termino=termino_busqueda_raw)
    
    return render_template('resultados.html', resultados=resultados, termino=termino_busqueda_raw)

# --- RUTA PARA MOSTRAR LA TABLA DEL EXCEL ---
@app.route('/excel')
def mostrar_excel():
    try:
        limite = int(request.args.get('limite', 100))
    except ValueError:
        limite = 100

    try:
        pagina = int(request.args.get('pagina', 1))
        if pagina < 1:
            pagina = 1
    except ValueError:
        pagina = 1

    busqueda = request.args.get('busqueda', '')
    estado = request.args.get('estado', 'todos')

    datos_excel_completos = leer_excel()
    if datos_excel_completos is None:
        return "Error: No se pudo leer el archivo Excel. Revisa la ruta en el archivo app.py.", 500

    # 🔽 Cargar estados desde la base de datos
    import sqlite3
    conn = sqlite3.connect('marcados.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT cedula, contrato, factura, estado FROM marcados")
    estado_raw = cursor.fetchall()
    conn.close()

    estado_map = {
        (str(e['cedula']), str(e['contrato']), str(e['factura'])): e['estado']
        for e in estado_raw
    }

    # 🔽 Agregar campo 'estado_marcado' a cada fila
    for fila in datos_excel_completos:
        clave = (str(fila.get('CEDULA', '')), str(fila.get('CONTRATO', '')), str(fila.get('FACTURA', '')))
        fila['estado_marcado'] = estado_map.get(clave, 'sin_marcar')

    # 🔽 Filtrado por texto en cualquier columna
    if busqueda:
        busqueda = busqueda.lower()
        filas_filtradas = [
            fila for fila in datos_excel_completos
            if any(busqueda in str(valor).lower() for valor in fila.values() if valor is not None)
        ]
    else:
        filas_filtradas = datos_excel_completos

    # 🔽 Filtrado por estado marcado
    if estado == 'encontrado':
        filas_filtradas = [fila for fila in filas_filtradas if fila.get('estado_marcado') == 'encontrado']
    elif estado == 'no_encontrado':
        filas_filtradas = [fila for fila in filas_filtradas if fila.get('estado_marcado') == 'no_encontrado']
    elif estado == 'sin_marcar':
        filas_filtradas = [fila for fila in filas_filtradas if fila.get('estado_marcado') == 'sin_marcar']

    total_filas = len(filas_filtradas)
    total_paginas = (total_filas + limite - 1) // limite
    inicio = (pagina - 1) * limite
    fin = inicio + limite
    filas_a_mostrar = filas_filtradas[inicio:fin]

    return render_template(
        'excel.html',
        filas=filas_a_mostrar,
        limite=limite,
        busqueda=busqueda,
        estado=estado,
        pagina=pagina,
        total_paginas=total_paginas,
        total_filas=total_filas
    )

@app.route('/marcar_fila', methods=['POST'])
def marcar_fila():
    cedula = request.form.get('cedula', '').strip()
    contrato = request.form.get('contrato', '').strip()
    factura = request.form.get('factura', '').strip()
    estado = request.form.get('accion', '').strip()

    if not cedula or not contrato or not factura or not estado:
        return "Datos incompletos", 400

    conn = sqlite3.connect('marcados.db')
    cursor = conn.cursor()

    # Buscar si ya existe un registro para esa combinación
    cursor.execute("""
        SELECT id FROM marcados
        WHERE cedula = ? AND contrato = ? AND factura = ?
    """, (cedula, contrato, factura))
    existente = cursor.fetchone()

    if existente:
        cursor.execute("""
            UPDATE marcados
            SET estado = ?, timestamp = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (estado, existente[0]))
    else:
        cursor.execute("""
            INSERT INTO marcados (cedula, contrato, factura, estado)
            VALUES (?, ?, ?, ?)
        """, (cedula, contrato, factura, estado))

    conn.commit()
    conn.close()

    # Redirigir de nuevo a la tabla con los mismos filtros
    return redirect(request.referrer or url_for('mostrar_excel'))

# --- RUTA PARA MANEJAR LA BÚSQUEDA DESDE LA TABLA EXCEL ---
@app.route('/buscar_fila', methods=['POST'])
def buscar_fila_excel():
    """
    Recibe los datos de una fila del Excel y realiza una búsqueda general en Alfresco,
    igual que el buscador principal.
    """
    cedula = request.form.get('CEDULA', '')
    contrato = request.form.get('CONTRATO', '')
    nombre = request.form.get('NAME', '')
    next_url = request.form.get('next') or url_for('mostrar_excel')

    identificador = cedula or contrato

    if not identificador:
        return redirect(next_url)

    print(f"Buscando en Alfresco con el término: {identificador}")
    terminos = identificador.strip().split()
    resultados = alfresco_service.buscar_archivos_generico(terminos)

    if not resultados:
        return render_template(
            'resultados.html',
            resultados=[],
            termino=identificador,
            error=f"No se encontraron resultados para '{identificador}'.",
            volver_a=next_url
        )

    return render_template(
        'resultados.html',
        resultados=resultados,
        termino=f"{identificador} ({nombre})",
        volver_a=next_url
    )

@app.route('/contenido/<node_id>')
def ver_contenido_carpeta(node_id):
    """
    Muestra el contenido de una carpeta específica, usando búsqueda recursiva.
    """
    resultados = alfresco_service.obtener_contenido_recursivo(node_id)
    if resultados is None:
        return render_template('resultados.html', resultados=[], error="No se pudo obtener el contenido de la carpeta.")
    return render_template('resultados.html', resultados=resultados, termino=f"Contenido de carpeta {node_id}")

#Ruta para busqueda y descarga de archivos desde script externo
@app.route('/api/search', methods=['POST'])
def api_busqueda():
    termino_busqueda_raw = request.json.get('termino', '')
    terminos = termino_busqueda_raw.split()

    if not terminos:
        return {'error': 'No se proporcionó ningún término'}, 400

    resultados = alfresco_service.buscar_archivos_generico(terminos)

    if resultados is None:
        return {'error': 'Error al conectar con Alfresco'}, 500

    # Extraer solo info necesaria: nodeId y nombre
    archivos = []
    for r in resultados:
        entry = r.get('entry', {})
        if entry.get('isFile'):
            archivos.append({
                'nodeId': entry.get('id'),
                'name': entry.get('name')
            })

    return {'resultados': archivos}, 200

@app.route('/view/<node_id>')
def visualizar_archivo(node_id):
    response_obj = alfresco_service.get_file_content(node_id, for_inline_view=True)
    if response_obj and response_obj.status_code == 200:
        contenido = b''.join(response_obj.iter_content())

        # Detectar nombre del archivo si es posible
        headers = dict(response_obj.headers)
        filename = node_id
        if 'Content-Disposition' in headers:
            parts = headers['Content-Disposition'].split('filename=')
            if len(parts) > 1:
                filename = parts[1].strip('";')

        # Detectar extensión si no tiene
        if '.' not in filename:
            content_type_header = headers.get('Content-Type', '')
            if 'pdf' in content_type_header:
                filename += '.pdf'
            elif 'tiff' in content_type_header or 'tif' in content_type_header:
                filename += '.tif'
            else:
                filename += '.bin'

        # Detectar MIME según la extensión
        content_type = detectar_tipo_mime(filename)

        # Si es PDF
        if filename.lower().endswith('.pdf'):
            if not es_pdf_valido(contenido):
                return "El archivo PDF está dañado o no se puede visualizar.", 415
            return Response(
                contenido,
                mimetype='application/pdf',
                headers={'Content-Disposition': f'inline; filename="{filename}"'}
            )

        # Si es TIFF
        elif filename.lower().endswith(('.tif', '.tiff')):
            convertido = convertir_tiff_a_png(contenido)
            if convertido:
                return Response(
                    convertido,
                    mimetype='image/png',
                    headers={'Content-Disposition': f'inline; filename="{node_id}.png"'}
                )
            else:
                return "No se pudo convertir el archivo TIFF.", 500

        # Por defecto: cualquier otro tipo
        return Response(
            contenido,
            mimetype=content_type,
            headers={'Content-Disposition': f'inline; filename="{filename}"'}
        )

    return "Error: No se pudo obtener el archivo para visualizar.", 404

@app.route('/download/<node_id>')
def descargar_archivo(node_id):
    response_obj = alfresco_service.get_file_content(node_id, for_inline_view=False)
    if response_obj and response_obj.status_code == 200:
        headers = dict(response_obj.headers)

        # Obtener el nombre del archivo desde el header o usar el node_id
        filename = node_id
        if 'Content-Disposition' in headers:
            parts = headers['Content-Disposition'].split('filename=')
            if len(parts) > 1:
                filename = parts[1].strip('";')

        # Forzar extensión .tif si no tiene
        if '.' not in filename:
            filename += '.tif'

        # Detectar tipo MIME
        content_type = detectar_tipo_mime(filename)

        # Forzar encabezado para descarga
        headers['Content-Disposition'] = f'attachment; filename="{filename}"'
        headers['Content-Type'] = content_type

        return Response(stream_with_context(response_obj.iter_content(chunk_size=1024*1024)), headers=headers)

    return "Error: No se pudo obtener el archivo para descargar.", 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=False)
