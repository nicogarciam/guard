# test_mqtt.py
import time
import mqtt_manager
import hardware

def accionar_rele():
    """Callback de prueba que acciona el relé real/simulado de hardware.py."""
    print("\n🔔 [CALLBACK] ¡Orden de apertura recibida!")
    hardware.abrir_porton()

if __name__ == "__main__":
    print("🧪 Iniciando prueba de MQTT usando 'mqtt_manager' y 'hardware'...")
    print("ℹ️ Nota: Se utilizarán los parámetros y credenciales configurados en 'config.py'.")
    
    # Inicializa el cliente MQTT y pasa la función de hardware.py que acciona el relé
    mqtt_manager.iniciar_mqtt(on_abrir_callback=accionar_rele)
    
    print("👂 Escuchando comandos en el tópico. Presiona Ctrl + C para detener...")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Deteniendo la prueba...")
        mqtt_manager.detener_mqtt()
        print("✅ Prueba finalizada limpiamente.")