# test_lpr_mqtt.py
import sys
import time
import os
from datetime import datetime
import config
import storage
import mqtt_manager
from lpr_processor import detectar_patente

def callback_vacio():
    pass

if __name__ == "__main__":
    # 1. Determinar imagen a usar
    ruta_imagen = None
    if len(sys.argv) > 1:
        ruta_imagen = sys.argv[1]
    else:
        # Buscar en la carpeta imgs
        posibles_rutas = [
            "patente.png",
            os.path.join("imgs", "patente_01.jpg"),
            os.path.join("imgs", "patente_02.png"),
            os.path.join("imgs", "patente_03.png"),
            os.path.join("imgs", "patente_04.jpg")
        ]
        for ruta in posibles_rutas:
            if os.path.exists(ruta):
                ruta_imagen = ruta
                break

    if not ruta_imagen or not os.path.exists(ruta_imagen):
        print("❌ Error: No se encontró ninguna imagen de prueba.")
        print("Por favor, especifica una imagen: python test_lpr_alpr.py [ruta_imagen]")
        sys.exit(1)

    print(f"🧪 Iniciando prueba de LPR + MQTT con la imagen: {ruta_imagen}")
    
    # 2. Ejecutar cada método
    resultados = {}
        
    # 2. Ejecutar reconocimiento de patentes (LPR)
    print("🔍 Procesando imagen con el motor LPR...")
    resultado_lpr = detectar_patente(ruta_imagen)
    patente_detectada = resultado_lpr.get("plate") if resultado_lpr else None
    
    # 3. Cargar la lista local de autorizados y verificar
    patentes_autorizadas = storage.cargar_patentes_locales()
    autorizado = False
    
    if patente_detectada:
        autorizado = patente_detectada in patentes_autorizadas
        print(f"📋 Resultado LPR: Patente '{patente_detectada}' | Autorizada: {'SÍ' if autorizado else 'NO'}")
    else:
        print("⚠️ Resultado LPR: No se logró reconocer ningún formato de patente válido.")
        
    # 4. Iniciar conexión MQTT y configurar TLS
    print("📡 Conectando al broker MQTT...")
    mqtt_manager.iniciar_mqtt(on_abrir_callback=callback_vacio)
    
    # Damos 2 segundos para asegurar la conexión de red con HiveMQ Cloud
    time.sleep(2)
    
    # 5. Construir y enviar el payload con el resultado
    payload_resultado = {
        "evento": "LPR_ANALISIS_TEST",
        "archivo_origen": os.path.basename(ruta_imagen),
        "patente_detectada": patente_detectada,
        "detalles_lpr": resultado_lpr,
        "autorizado": autorizado,
        "timestamp": datetime.now().isoformat()
    }
    
    print(f"⬆️ Enviando resultado de análisis al tópico '{config.TOPIC_ESTADO}'...")
    mqtt_manager.publicar_mensaje(config.TOPIC_ESTADO, payload_resultado)
    
    # Esperamos 1 segundo para asegurar la entrega del mensaje
    time.sleep(1)
    
    # 6. Desconexión ordenada
    mqtt_manager.detener_mqtt()
    print("🏁 Prueba de LPR + MQTT finalizada correctamente.")
