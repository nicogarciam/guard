# test_pir_camara.py
import cv2
import time
import os
from datetime import datetime
import config
import hardware

# --- CONFIGURACIÓN DE PRUEBA ---
CARPETA_GUARDADO = "pruebas_camara"
TIEMPO_EXPOSICION = 1.5      # Segundos para estabilizar luz/exposición de la cámara
TIEMPO_ESPERA_REBOTE = 5     # Pausa anti-rebote

# Crear carpeta de pruebas si no existe
os.makedirs(CARPETA_GUARDADO, exist_ok=True)

print("🚀 Iniciando prueba de Cámara + PIR utilizando componentes...")
print(f"📂 Las imágenes se guardarán en: ./{CARPETA_GUARDADO}/")
print("👂 Esperando movimiento del sensor PIR... (Presiona Ctrl+C para salir)")

try:
    while True:
        # Espera utilizando la abstracción del hardware (soporta simulación en PC)
        hardware.esperar_movimiento()
        print("\n🚨 ¡Movimiento detectado! Preparando cámara...")
        
        # Inicializar cámara utilizando el índice de la configuración centralizada
        cap = cv2.VideoCapture(config.CAMARA_INDEX)
        
        if not cap.isOpened():
            print("❌ ERROR: No se pudo acceder a la cámara USB. Verifica config.CAMARA_INDEX.")
            break
            
        # Espera para estabilizar la luz de la cámara
        time.sleep(TIEMPO_EXPOSICION)
        ret, frame = cap.read()
        cap.release()
        
        if ret:
            # Generar nombre del archivo
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nombre_archivo = f"captura_{timestamp}.jpg"
            ruta_completa = os.path.join(CARPETA_GUARDADO, nombre_archivo)
            
            # Guardar la imagen de prueba
            cv2.imwrite(ruta_completa, frame)
            print(f"✅ ¡Foto guardada exitosamente!: {ruta_completa}")
        else:
            print("❌ ERROR: La cámara no devolvió ningún frame (imagen vacía).")
            
        # Anti-rebote y espera de fin de movimiento utilizando el componente de hardware
        print(f"⏳ Esperando {TIEMPO_ESPERA_REBOTE} segundos para reiniciar el sensor...")
        time.sleep(TIEMPO_ESPERA_REBOTE)
        hardware.esperar_sin_movimiento()
        print("👂 Sensor en reposo. Esperando próximo movimiento...")

except KeyboardInterrupt:
    print("\n🛑 Prueba detenida por el usuario. ¡Hasta luego!")
except Exception as e:
    print(f"\n💥 Ocurrió un error inesperado: {e}")