# storage.py
import os
import json
from datetime import datetime
import config

def inicializar_directorios():
    """Crea la carpeta de pendientes si no existe."""
    os.makedirs(config.PENDING_DIR, exist_ok=True)

def cargar_patentes_locales():
    """Carga la lista de patentes autorizadas desde el archivo local."""
    try:
        with open(config.DB_LOCAL, 'r') as f:
            data = json.load(f)
            return set(data.get("patentes", []))
    except (FileNotFoundError, json.JSONDecodeError):
        return set()

def guardar_patentes_locales(patentes_list):
    """Guarda una lista de patentes en el archivo local de caché de forma atómica."""
    temp_file = config.DB_LOCAL + ".tmp"
    try:
        with open(temp_file, 'w') as f:
            json.dump({"patentes": list(set(patentes_list))}, f)
        os.replace(temp_file, config.DB_LOCAL)
    except Exception as e:
        print(f"❌ Error al guardar caché de patentes localmente: {e}")

def guardar_en_cola_reportes(img_path, patente, estado):
    """Guarda la imagen y sus metadatos en la cola local para envío diferido."""
    inicializar_directorios()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Nombre seguro para archivos
    safe_patente = patente if patente else "NO_LEIDA"
    safe_patente = "".join(c for c in safe_patente if c.isalnum())
    
    json_name = f"{timestamp}_{estado}_{safe_patente}.json"
    json_path = os.path.join(config.PENDING_DIR, json_name)
    
    img_name = f"{timestamp}_{estado}_{safe_patente}.jpg"
    final_img_path = os.path.join(config.PENDING_DIR, img_name)
    
    try:
        # Movimiento atómico de la imagen temporal a la carpeta de pendientes
        if os.path.exists(img_path):
            os.replace(img_path, final_img_path)
        else:
            print(f"⚠️ Advertencia: No se encontró la imagen temporal {img_path} para mover.")
            
        metadata = {
            "timestamp": datetime.now().isoformat(),
            "patente": patente,
            "estado": estado,  # "EXITO", "FALLO" o "FALLO_LECTURA"
            "imagen": img_name
        }
        with open(json_path, 'w') as f:
            json.dump(metadata, f)
        print(f"💾 Reporte guardado en cola local: {estado} - {patente if patente else 'Sin Patente'}")
    except Exception as e:
        print(f"❌ Error al guardar el reporte en cola local: {e}")
