# config.py
import sys
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

# --- CONFIGURACIÓN DE PINES Y HARDWARE ---
PIN_PIR = 17
PIN_RELE = 27
TIEMPO_ACTIVACION_RELE = 0.5 
CAMARA_INDEX = 0

# --- CONFIGURACIÓN DE DIRECTORIOS Y ARCHIVOS ---
DB_LOCAL = "patentes.json"
PENDING_DIR = "pendientes_uploads"
CAPTURES_DIR = "capturas"

# --- CONFIGURACIÓN MQTT (HIVEMQ CLOUD) ---
MQTT_BROKER = "2d2715a472da427cb5a4b346706179af.s1.eu.hivemq.cloud"
MQTT_PORT = 8883  # HiveMQ Cloud usa TLS en puerto 8883
MQTT_USER = "rpi_porton"
MQTT_PASS = "Guard123qwe"
MQTT_TOKEN_SEGURO = "mi_secreto_super_seguro_123"

TOPIC_COMANDO = "mi_porton/comando"
TOPIC_ESTADO = "mi_porton/estado"
TOPIC_EVENTO = "mi_porton/evento"

# --- ENDPOINTS API ---
URL_ENDPOINT_PATENTES = "https://tu-servidor.com/api/patentes-autorizadas"
URL_ENDPOINT_REPORTES = "https://tu-servidor.com/api/reportes-acceso"
API_TOKEN = "tu_token_secreto"

# --- INTERVALOS (SEGUNDOS) ---
INTERVALO_ACTUALIZACION_PATENTES = 3600  # 1 hora
INTERVALO_SUBIDA_REPORTES = 30             # 30 segundos

OPENALPR_KEY = "fe561fb99a23ac74c8b371437d442114dcfd0166"
LPR_METHOD = "snapshot_cloud"
OPENALPR_COUNTRY = "ar"

SNAPSHOT_CLOUD_API_TOKEN = "edd19dc949b7968c4d857dafe858a26a41f04344"