ssh ngarciam@192.168.0.242

# Config

https://console.hivemq.cloud/

https://app.platerecognizer.com/

https://api.platerecognizer.com/v1/plate-reader/



sudo apt update
sudo apt install python3-opencv python3-gpiozero -y
sudo apt install python3-pip -y
pip3 install requests paho-mqtt opencv-python-headless gpiozero
pip3 install paho-mqtt

sudo apt install openalpr openalpr-daemon openalpr-utils libopenalpr-dev

python3 -c "import cv2, requests, paho.mqtt.client, gpiozero; print('✅ ¡Todas las librerías instaladas correctamente!')"


# Actualizar e instalar Tesseract OCR y sus datos en español/inglés
sudo apt-get update
sudo apt-get install tesseract-ocr tesseract-ocr-spa tesseract-ocr-eng -y

# Instalar la librería de Python (asegúrate de estar en tu entorno virtual si usas uno)
pip install pytesseract opencv-python-headless

0 3 * * * find /ruta/a/tu/carpeta/pendientes_uploads -type f -name "*.jpg" -mtime +7 -delete
0 3 * * * find /ruta/a/tu/carpeta/pendientes_uploads -type f -name "*.json" -mtime +7 -delete



python3 test_pir_camara.py

sudo python3 main.py

