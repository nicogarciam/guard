# api_client.py
import os
import glob
import requests
import json
import config

def descargar_patentes_autorizadas():
    """Descarga la lista de patentes autorizadas del servidor remoto."""
    try:
        headers = {"Authorization": f"Bearer {config.API_TOKEN}"}
        response = requests.get(config.URL_ENDPOINT_PATENTES, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data.get("patentes", [])
        else:
            print(f"⚠️ Servidor respondió con código {response.status_code} al actualizar patentes.")
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Error al conectar con el servidor para actualizar patentes: {e}")
    return None

def subir_reportes_pendientes():
    """Busca reportes encolados localmente y los sube uno a uno."""
    # Buscar todos los archivos .json en la carpeta de pendientes
    json_files = glob.glob(os.path.join(config.PENDING_DIR, "*.json"))
    
    for json_path in json_files:
        try:
            with open(json_path, 'r') as f:
                metadata = json.load(f)
            
            img_path = os.path.join(config.PENDING_DIR, metadata["imagen"])
            
            if not os.path.exists(img_path):
                print(f"⚠️ Imagen faltante para {json_path}. Eliminando JSON huérfano.")
                os.remove(json_path)
                continue

            # Preparar la petición multipart/form-data
            with open(img_path, 'rb') as img_file:
                files = {
                    'imagen': (metadata["imagen"], img_file, 'image/jpeg')
                }
                data_payload = {
                    'timestamp': metadata["timestamp"],
                    'patente': metadata["patente"] or "",
                    'estado': metadata["estado"]
                }
                headers = {"Authorization": f"Bearer {config.API_TOKEN}"}

                print(f"⬆️ Enviando reporte: {metadata['estado']} - {metadata['patente']}")
                
                # Timeout largo para subida de fotos
                response = requests.post(
                    config.URL_ENDPOINT_REPORTES, 
                    files=files, 
                    data=data_payload, 
                    headers=headers, 
                    timeout=15
                )
                
                if response.status_code == 200:
                    print("✅ Reporte enviado con éxito. Limpiando archivos locales.")
                    # El bloque 'with' asegura que el archivo de imagen ya está cerrado
                    os.remove(img_path)
                    os.remove(json_path)
                else:
                    print(f"⚠️ El servidor rechazó el reporte (HTTP {response.status_code}). Se reintentará luego.")
                    
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Error de red/conexión subiendo reportes: {e}. Se reintentará luego.")
            break  # Detener el ciclo para no spammear en caso de caída de red
        except Exception as e:
            print(f"❌ Error inesperado procesando {json_path}: {e}")
