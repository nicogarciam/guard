# mqtt_manager.py
import json
from datetime import datetime
import paho.mqtt.client as mqtt
import config

mqtt_client = None
_on_abrir_callback = None

def publicar_estado(estado):
    """Publica el estado actual en el tópico MQTT configurado."""
    global mqtt_client
    if mqtt_client and mqtt_client.is_connected():
        payload = {"estado": estado, "timestamp": datetime.now().isoformat()}
        try:
            mqtt_client.publish(config.TOPIC_ESTADO, json.dumps(payload), retain=True)
        except Exception as e:
            print(f"❌ Error al publicar estado MQTT: {e}")
    else:
        print(f"⚠️ Advertencia: No se pudo publicar el estado '{estado}'. El cliente MQTT no está conectado.")

def publicar_mensaje(topic, payload):
    """Publica un diccionario/objeto JSON en un tópico específico."""
    global mqtt_client
    if mqtt_client and mqtt_client.is_connected():
        try:
            mqtt_client.publish(topic, json.dumps(payload), retain=False)
            print(f"📤 Mensaje publicado exitosamente en el tópico '{topic}': {payload.get('event') or payload}")
        except Exception as e:
            print(f"❌ Error al publicar en {topic}: {e}")
    else:
        print(f"⚠️ Advertencia: Intento de publicar en '{topic}' falló. El cliente MQTT no está conectado. Mensaje: {payload.get('event') or payload}")

def _on_connect(client, userdata, flags, rc):
    """Callback ejecutado cuando se logra conectar al broker."""
    if rc == 0:
        print("✅ Conectado al Broker MQTT exitosamente.")
        client.subscribe(config.TOPIC_COMANDO)
        publicar_estado("EN_LINEA")
    else:
        print(f"❌ Fallo al conectar a MQTT. Código: {rc}")

def _on_message(client, userdata, msg):
    """Callback ejecutado al recibir un mensaje del tópico comando."""
    global _on_abrir_callback
    try:
        payload = json.loads(msg.payload.decode())
        
        # 1. Validar seguridad con el token
        if payload.get("token") != config.MQTT_TOKEN_SEGURO:
            print("⛔ Intento de apertura remota rechazado: Token inválido.")
            return
            
        # 2. Validar acción
        if payload.get("accion") == "ABRIR":
            print("📱 Comando remoto recibido: Abriendo portón...")
            if _on_abrir_callback:
                _on_abrir_callback()
            publicar_estado("ABIERTO_REMOTO")
        else:
            print(f"⚠️ Comando remoto desconocido: {payload.get('accion')}")
            
    except json.JSONDecodeError:
        print("❌ Error al decodificar mensaje MQTT.")
    except Exception as e:
        print(f"❌ Error procesando mensaje MQTT: {e}")

def iniciar_mqtt(on_abrir_callback):
    """Inicializa, configura TLS y conecta el cliente MQTT en segundo plano."""
    global mqtt_client, _on_abrir_callback
    _on_abrir_callback = on_abrir_callback
    
    mqtt_client = mqtt.Client(client_id="rpi_porton_01")
    mqtt_client.username_pw_set(config.MQTT_USER, config.MQTT_PASS)
    
    # ¡CRUCIAL PARA HIVEMQ CLOUD! Habilitar cifrado TLS
    try:
        mqtt_client.tls_set()
    except Exception as e:
        print(f"⚠️ Error al configurar TLS para MQTT: {e}")
        
    mqtt_client.on_connect = _on_connect
    mqtt_client.on_message = _on_message
    
    mqtt_client.reconnect_delay_set(min_delay=1, max_delay=120)
    
    try:
        mqtt_client.connect_async(config.MQTT_BROKER, config.MQTT_PORT, keepalive=60)
        mqtt_client.loop_start()  # Inicia el bucle de red en un hilo secundario
    except Exception as e:
        print(f"❌ No se pudo iniciar MQTT: {e}")

def detener_mqtt():
    """Detiene ordenadamente la conexión con el broker."""
    global mqtt_client
    if mqtt_client:
        print("🛑 Desconectando de MQTT...")
        publicar_estado("OFFLINE")
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
        print("✅ Desconexión limpia completada en MQTT.")
