# main.py
import time
import threading
import config
import storage
import hardware
import api_client
import mqtt_manager
import camera_manager

def hilo_actualizacion_patentes():
    """Hilo secundario que descarga la lista de patentes autorizadas periódicamente."""
    print("🔄 Hilo de actualización de patentes iniciado.")
    while True:
        patentes = api_client.descargar_patentes_autorizadas()
        if patentes is not None:
            storage.guardar_patentes_locales(patentes)
        time.sleep(config.INTERVALO_ACTUALIZACION_PATENTES)

def hilo_subida_reportes():
    """Hilo secundario que procesa los reportes pendientes de subida periódicamente."""
    print("📤 Hilo de subida de reportes iniciado.")
    while True:
        api_client.subir_reportes_pendientes()
        time.sleep(config.INTERVALO_SUBIDA_REPORTES)

if __name__ == "__main__":
    print("🚀 Iniciando Sistema de Control de Acceso Avanzado...")
    
    # 1. Crear directorios necesarios
    storage.inicializar_directorios()
    
    # 2. Carga inicial de patentes locales para contingencia offline
    patentes_actuales = storage.cargar_patentes_locales()
    print(f"🔑 Patentes autorizadas cargadas en memoria: {len(patentes_actuales)}")
    
    # 3. Iniciar el cliente MQTT (pasando callback de apertura remota)
    mqtt_manager.iniciar_mqtt(on_abrir_callback=hardware.abrir_porton)
    
    # 4. Lanzar hilos de red en segundo plano (daemon threads)
    threading.Thread(target=hilo_actualizacion_patentes, daemon=True).start()
    threading.Thread(target=hilo_subida_reportes, daemon=True).start()
    
    print("👂 Escuchando sensor PIR y tópicos MQTT... (Presiona Ctrl+C para detener)")
    try:
        while True:
            # Esperar a que el PIR detecte movimiento
            hardware.esperar_movimiento()
            
            # Capturar y procesar evento
            camera_manager.capturar_y_procesar()
            
            # Filtro anti-rebote simple
            time.sleep(3)
            
            # Esperar a que se libere la zona de detección
            hardware.esperar_sin_movimiento()
            
    except KeyboardInterrupt:
        print("\n🛑 Deteniendo sistema de forma segura...")
        mqtt_manager.detener_mqtt()
        print("👋 Sistema apagado correctamente.")