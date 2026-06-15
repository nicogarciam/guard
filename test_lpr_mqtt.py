# test_lpr_mqtt.py
import sys
import time
import os
from datetime import datetime
import config
import storage
import mqtt_manager
from lpr_processor import detectar_patente
import plate_validator

def callback_vacio():
    pass

if __name__ == "__main__":
    # 1. Determinar imágenes a usar
    imagenes_a_procesar = []
    if len(sys.argv) > 1:
        ruta_arg = sys.argv[1]
        if os.path.exists(ruta_arg):
            imagenes_a_procesar.append(ruta_arg)
        else:
            print(f"❌ Error: La imagen/ruta '{ruta_arg}' no existe.")
            sys.exit(1)
    else:
        # Buscar todas las imágenes en la carpeta 'imgs'
        import glob
        patrones = [
            os.path.join("imgs", "*.jpg"),
            os.path.join("imgs", "*.jpeg"),
            os.path.join("imgs", "*.png")
        ]
        for patron in patrones:
            imagenes_a_procesar.extend(glob.glob(patron))
            
    if not imagenes_a_procesar:
        print("❌ Error: No se encontró ninguna imagen de prueba en la carpeta 'imgs'.")
        sys.exit(1)

    print(f"🧪 Iniciando prueba de LPR + MQTT para {len(imagenes_a_procesar)} imágenes...")
    
    # 2. Iniciar conexión MQTT una sola vez
    print("📡 Conectando al broker MQTT...")
    mqtt_manager.iniciar_mqtt(on_abrir_callback=callback_vacio)
    
    # Damos 2 segundos para asegurar la conexión de red con HiveMQ Cloud
    time.sleep(2)
    
    # 3. Procesar cada imagen
    for i, ruta_imagen in enumerate(imagenes_a_procesar, 1):
        print(f"\n📸 [{i}/{len(imagenes_a_procesar)}] Procesando imagen: {ruta_imagen}")
        
        payload = {
            "event": "LPR_ANALYSIS_TEST_INIT",
            "dsc": "Procesando imagen",
            "source_file": os.path.basename(ruta_imagen),
            "timestamp": datetime.now().isoformat()
        }
        
        mqtt_manager.publicar_mensaje(config.TOPIC_EVENTO, payload)


        # Ejecutar reconocimiento de patentes (LPR)
        resultado_lpr = detectar_patente(ruta_imagen)
        patente_detectada = resultado_lpr.get("plate") if resultado_lpr else None
        
        autorizado = False
        if patente_detectada:
            autorizado = plate_validator.validar_patente(resultado_lpr)
            print(f"📋 Resultado LPR: Patente '{patente_detectada}' | Autorizada: {'SÍ' if autorizado else 'NO'}")
        else:
            print("⚠️ Resultado LPR: No se logró reconocer ningún formato de patente válido.")
            
        
        # Esperamos 1.5 segundos entre imágenes para asegurar el envío y orden en el broker
        time.sleep(1.5)
        
    # 4. Desconexión ordenada
    mqtt_manager.detener_mqtt()
    print("🏁 Prueba de LPR + MQTT para todas las imágenes finalizada correctamente.")
