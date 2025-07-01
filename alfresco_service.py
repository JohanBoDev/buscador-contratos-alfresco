# alfresco_service.py

import requests
import logging

# --- Configuración de la Conexión ---
ALFRESCO_URL = "https://alfrdms.tigo.com.co/alfresco"
USERNAME = "johan.Bohorquez" 
PASSWORD = "Tigo2025*" 

# --- EXTENSIONES VÁLIDAS ---
EXTENSIONES_VALIDAS = ('.pdf', '.tif', '.tiff')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [AlfrescoService] - %(message)s')


def buscar_archivos_generico(terminos):
    """
    Búsqueda genérica que requiere que TODOS los términos estén presentes.
    """
    if not terminos: return []

    # Unimos los términos con AND para una búsqueda precisa
    search_query = " AND ".join(terminos)

    payload = {
        "query": {
            "query": search_query,
            "language": "afts"
        },
        "include": ["path", "properties"],
        "paging": {"maxItems": 100}
    }
    
    search_endpoint = f"{ALFRESCO_URL}/api/-default-/public/search/versions/1/search"
    logging.info(f"Enviando búsqueda genérica con la consulta: '{search_query}'")
    
    try:
        response = requests.post(search_endpoint, json=payload, auth=(USERNAME, PASSWORD), timeout=30)
        response.raise_for_status()
        return response.json().get('list', {}).get('entries', [])
    except requests.exceptions.RequestException as e:
        error_details = f"URL: {e.request.url}"
        if e.response is not None:
            error_details += f", Status: {e.response.status_code}, Response: {e.response.text}"
        logging.error(f"Error de API en búsqueda genérica: {e}. Detalles: {error_details}")
        return None

def encontrar_carpeta_cliente(identificador):
    """Busca tanto archivos como carpetas relacionados con un identificador."""
    payload = {
        "query": { "query": f'name:*{identificador}*' },
        "include": ["id", "name", "isFolder", "isFile", "path"],
        "paging": {"maxItems": 100}
    }
    search_endpoint = f"{ALFRESCO_URL}/api/-default-/public/search/versions/1/search"
    try:
        response = requests.post(search_endpoint, json=payload, auth=(USERNAME, PASSWORD), timeout=20)
        response.raise_for_status()
        return response.json().get('list', {}).get('entries', [])
    except requests.exceptions.RequestException as e:
        logging.error(f"Error de API buscando carpeta: {e}")
        return None

def obtener_contenido_recursivo(start_node_id):
    archivos_encontrados = []
    carpetas_a_visitar = [start_node_id]

    while carpetas_a_visitar:
        current_folder_id = carpetas_a_visitar.pop(0)
        children_endpoint = f"{ALFRESCO_URL}/api/-default-/public/alfresco/versions/1/nodes/{current_folder_id}/children"

        try:
            response = requests.get(
                children_endpoint,
                auth=(USERNAME, PASSWORD),
                params={"include": ["properties", "path", "isFolder", "isFile"]}
            )
            response.raise_for_status()
            entries = response.json().get('list', {}).get('entries', [])

            for item in entries:
                entry = item['entry']
                if entry.get('isFolder'):
                    archivos_encontrados.append(item)
                    carpetas_a_visitar.append(entry['id'])
                elif entry.get('isFile'):
                    archivos_encontrados.append(item)
        except requests.exceptions.RequestException as e:
            logging.error(f"Error obteniendo hijos de la carpeta {current_folder_id}: {e}")
            continue

    return archivos_encontrados


def get_file_content(node_id, for_inline_view=False):
    """Obtiene el contenido de un archivo específico."""
    if not node_id: return None
    content_endpoint = f"{ALFRESCO_URL}/api/-default-/public/alfresco/versions/1/nodes/{node_id}/content"
    params = {'attachment': 'false'} if for_inline_view else {}
    try:
        response = requests.get(
            content_endpoint, params=params, auth=(USERNAME, PASSWORD), stream=True, timeout=30
        )
        response.raise_for_status()
        return response
    except requests.exceptions.RequestException as e:
        logging.error(f"Error de API obteniendo contenido: {e}")
        return None
