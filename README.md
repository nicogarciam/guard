ssh ngarciam@192.168.0.242
pass: Ng123qwe.

# Proyecto Guard (LPR & Webcams)

Este proyecto maneja la seguridad y accesos del predio, compuesto actualmente por dos servicios principales mediante una arquitectura de *Monorepo*:

1. **LPR Service (Reconocimiento de Patentes):** Control de acceso vehicular mediante cámaras, validación y apertura de barrera.
2. **Webcams Service (Streaming Online):** Transmisión y visualización de cámaras de seguridad en tiempo real.
3. **Frontend (Dashboards):** Interfaz web para visualizar las cámaras y los eventos LPR.

## Accesos Rápidos (URLs de Producción)

Una vez que los servicios están corriendo en la Raspberry (IP `192.168.0.242`), podés acceder a los dashboards desde cualquier dispositivo en la misma red:

- **Dashboard de Cámaras (En vivo):** [http://192.168.0.242:8080/webcams.html](http://192.168.0.242:8080/webcams.html)
- **Dashboard LPR (Eventos MQTT):** [http://192.168.0.242:8080/mqtt_client.html](http://192.168.0.242:8080/mqtt_client.html)
- **API interna de go2rtc (Diagnóstico):** [http://192.168.0.242:1984/](http://192.168.0.242:1984/)

## Estructura del Proyecto (Monorepo)

```text
guard/
├── core/                     # Lógica e infraestructura compartida
│   ├── camera_manager.py     # Manejo y reconexión de cámaras RTSP/HTTP
│   ├── storage.py            # Guardado de eventos o bases de datos locales
│   ├── api_client.py         # Interacción con APIs externas
│   └── config.py             # Configuración general y de entorno
│
├── services/                 # Aplicaciones independientes
│   ├── lpr/                  # Servicio actual de patentes
│   │   ├── main.py           # Entrypoint del LPR
│   │   ├── lpr_processor.py  # Detección y análisis
│   │   ├── hardware.py       # Control de barreras/PIR
│   │   ├── mqtt_manager.py   # Eventos de red
│   │   └── patentes.json     # BD local de autorizados
│   │
│   └── webcams/              # Nuevo servicio de streaming
│       ├── main.py           # Entrypoint de Webcams
│       └── stream_server.py  # Servidor de video (en desarrollo)
│
├── guard.service             # Unit file systemd para LPR
└── README.md                 # Este documento
```

---

## Enlaces Útiles
- HiveMQ: https://console.hivemq.cloud/
- PlateRecognizer Dashboard: https://app.platerecognizer.com/
- PlateRecognizer API: https://api.platerecognizer.com/v1/plate-reader/

## Configuración del Entorno (Raspberry Pi / Linux)

### 1. Librerías de Python e Instalación Base
```bash
sudo apt update
sudo apt install python3-opencv python3-gpiozero python3-pip -y
pip3 install requests paho-mqtt opencv-python-headless gpiozero pytesseract
```

### 2. Tesseract OCR y OpenALPR (Reconocimiento Local)
```bash
sudo apt-get install tesseract-ocr tesseract-ocr-spa tesseract-ocr-eng -y
sudo apt install openalpr openalpr-daemon openalpr-utils libopenalpr-dev
```

### 3. Verificar instalación
```bash
python3 -c "import cv2, requests, paho.mqtt.client, gpiozero; print('✅ ¡Todas las librerías instaladas correctamente!')"
```

## Limpieza Automática (Cron)
Para evitar llenar el disco con fotos de intentos fallidos, agregar al crontab (`crontab -e`):
```cron
0 3 * * * find /ruta/a/tu/carpeta/pendientes_uploads -type f -name "*.jpg" -mtime +7 -delete
0 3 * * * find /ruta/a/tu/carpeta/pendientes_uploads -type f -name "*.json" -mtime +7 -delete
```

---

## Ejecución de Servicios

### Configuración de Cámaras (Webcams)
El servicio de webcams utiliza `cameras.json` (ubicado en la raíz) para saber qué cámaras transmitir. Este archivo se debe llenar con los nombres y las URLs RTSP/HTTP.
El propio script de Python se encargará de descargar `go2rtc` y crear su archivo de configuración basándose en este JSON.

**Visualización del Cliente:**
Una vez iniciado el servicio de webcams, simplemente abrí el archivo `client/webcams.html` en cualquier navegador web. El cliente buscará dinámicamente qué cámaras están configuradas y las renderizará en una grilla usando WebRTC para latencia cero.

### Modo Manual
**LPR (Patentes):**
```bash
sudo python3 services/lpr/main.py
```
**Webcams (Streaming):**
```bash
sudo python3 services/webcams/main.py
```

### Gestión de Servicios (Systemd)

Para administrar los servicios en background, utiliza los siguientes comandos (reemplazar `guard` por `guard-webcams` o `guard-client` según corresponda):

- **Ver el estado:** `sudo systemctl status guard`
- **Iniciar:** `sudo systemctl start guard`
- **Detener:** `sudo systemctl stop guard`
- **Reiniciar:** `sudo systemctl restart guard`
- **Ver los logs en tiempo real:** `sudo journalctl -u guard -f`
