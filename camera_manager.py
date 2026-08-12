# camera_manager.py
import cv2
import time
import os
from datetime import datetime
import config
import storage
import hardware
from lpr_processor import detectar_patente
import mqtt_manager
import plate_validator

def capturar_y_procesar():
    """Realiza la captura de un frame de la cámara y procesa la detección de patentes."""
    print("🚨 Movimiento detectado! Iniciando captura de cámara...")
    storage.inicializar_directorios()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    capturas_dir = getattr(config, 'CAPTURES_DIR', 'capturas')
    img_temp_path = os.path.join(capturas_dir, f"captura_{timestamp}.jpg")
    
    # Abrir cámara
    cap = cv2.VideoCapture(config.CAMARA_INDEX)
    if not cap.isOpened():
        print("❌ Error: No se pudo abrir la cámara.")
        return
        
    time.sleep(1)  # Tiempo para que la cámara estabilice el brillo/exposición
    ret, frame = cap.read()
    cap.release()
    
    if ret:
        cv2.imwrite(img_temp_path, frame)
        print(f"📸 Imagen guardada en: {img_temp_path}")
        resultado_lpr = detectar_patente(img_temp_path)
        
        if resultado_lpr and resultado_lpr.get("plate"):
            patente_detectada = resultado_lpr["plate"]
            authorized = plate_validator.validar_patente(resultado_lpr)
            
            if authorized:
                print(f"🔓 Patente AUTORIZADA: {patente_detectada}. Abriendo portón...")
                storage.guardar_en_cola_reportes(img_temp_path, patente_detectada, "EXITO")
                hardware.abrir_porton()
            else:
                print(f"⛔ Patente NO autorizada: {patente_detectada}")
                storage.guardar_en_cola_reportes(img_temp_path, patente_detectada, "FALLO")
        else:
            print("⚠️ No se pudo leer ninguna patente válida en la captura.")
            storage.guardar_en_cola_reportes(img_temp_path, None, "FALLO_LECTURA")
    else:
        print("❌ Error al capturar imagen del dispositivo de cámara.")
