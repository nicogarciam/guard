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

def capturar_y_procesar(patentes_autorizadas):
    """Realiza la captura de un frame de la cámara y procesa la detección de patentes."""
    print("🚨 Movimiento detectado! Iniciando captura de cámara...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    img_temp_path = f"temp_{timestamp}.jpg"
    
    # Abrir cámara
    cap = cv2.VideoCapture(config.CAMARA_INDEX)
    if not cap.isOpened():
        print("❌ Error: No se pudo abrir la cámara.")
        return
        
    time.sleep(0.5)  # Tiempo para que la cámara estabilice el brillo/exposición
    ret, frame = cap.read()
    cap.release()
    
    if ret:
        cv2.imwrite(img_temp_path, frame)
        resultado_lpr = detectar_patente(img_temp_path)
        
        # 1. Evento de detección LPR (LPR_DETECTION)
        success = bool(resultado_lpr and resultado_lpr.get("plate"))
        lpr_payload = {
            "event": "LPR_DETECTION",
            "success": success,
            "result": resultado_lpr,
            "timestamp": datetime.now().isoformat()
        }
        print(f"📡 Publicando evento LPR_DETECTION por MQTT... Éxito: {success}")
        mqtt_manager.publicar_mensaje(config.TOPIC_ESTADO, lpr_payload)
        
        if success:
            patente_detectada = resultado_lpr["plate"]
            authorized = patente_detectada in patentes_autorizadas
            
            # 2. Evento de validación de patente (PLATE_VALIDATION)
            validation_payload = {
                "event": "PLATE_VALIDATION",
                "plate": patente_detectada,
                "authorized": authorized,
                "timestamp": datetime.now().isoformat()
            }
            print(f"📡 Publicando evento PLATE_VALIDATION por MQTT... Autorizado: {authorized}")
            mqtt_manager.publicar_mensaje(config.TOPIC_ESTADO, validation_payload)
            
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
            
        # Limpieza: si por alguna razón la imagen no se movió a pendientes_uploads, la eliminamos
        if os.path.exists(img_temp_path):
            try:
                os.remove(img_temp_path)
            except Exception as e:
                print(f"❌ Error al eliminar archivo temporal {img_temp_path}: {e}")
    else:
        print("❌ Error al capturar imagen del dispositivo de cámara.")
