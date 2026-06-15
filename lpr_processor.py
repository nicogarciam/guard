# lpr_processor.py
import cv2
import pytesseract
import re
import os
import subprocess
import json
import requests
import config
import mqtt_manager
from datetime import datetime

# Configuración de la ruta del ejecutable de Tesseract
pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'

def preprocesar_imagen(imagen):
    """Preprocesa la imagen para maximizar el contraste de la patente argentina."""
    gray = cv2.cvtColor(imagen, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    # Thresholding adaptativo es clave para patentes con reflejos o sombras
    thresh = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
    return closed

def normalizar_ocr(texto):
    """
    Corrige los errores más comunes de Tesseract en patentes argentinas 
    ANTES de validar con la expresión regular.
    """
    # Convertir todo a mayúsculas por seguridad
    texto = texto.upper()
    
    # En las posiciones de NÚMEROS (índices 3, 4, 5 en ambos formatos), 
    # es muy común que Tesseract lee 'O' o 'Q' en lugar de '0', e 'I' o 'L' en lugar de '1'.
    # Hacemos un reemplazo global inteligente:
    texto = texto.replace('O', '0').replace('Q', '0')
    texto = texto.replace('I', '1').replace('L', '1')
    texto = texto.replace('S', '5') # Menos frecuente, pero útil
    
    # Si el formato es Mercosur (2 letras, 3 números, 2 letras), la última letra a veces 
    # se lee mal, pero no la forzamos a número para no romper patentes reales que terminen en O o I.
    
    return texto

def detectar_patente_tesseract(ruta_imagen):
    """Procesa la imagen usando Tesseract OCR y devuelve el formato estructurado estándar."""
    try:
        img = cv2.imread(ruta_imagen)
        if img is None:
            return None
        
        processed_img = preprocesar_imagen(img)
        
        # psm 7: Trata la imagen como una sola línea de texto (ideal para patentes)
        # whitelist: Solo permite letras y números, ignora símbolos, puntos o guiones
        custom_config = r'--oem 3 --psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        
        texto_crudo = pytesseract.image_to_string(processed_img, config=custom_config)
        return {
            "vehicle": {
                "type": "",
                "score": 0.0,
                "color": ""
            },
            "plate": texto_crudo or ""
        }
    except Exception as e:
        print(f"❌ Error en Tesseract LPR: {e}")
        return None

def detectar_patente_openalpr_local(ruta_imagen):
    """Procesa la imagen usando OpenALPR local a través de CLI (alpr) y devuelve el formato estructurado estándar."""
    try:
        country = getattr(config, 'OPENALPR_COUNTRY', 'us')
        # Ejecutar el comando alpr con salida JSON (-j) y región/país (-c)
        cmd = ["alpr", "-j", "-c", country, ruta_imagen]
        resultado = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10)
        
        if resultado.returncode != 0:
            print(f"❌ Error al ejecutar OpenALPR local (código {resultado.returncode}): {resultado.stderr}")
            return None
            
        data = json.loads(resultado.stdout)
        results = data.get("results", [])
        plate = ""
        if results:
            # Retornar la patente con mayor confianza (el primer elemento)
            plate = results[0].get("plate", "")
            print(f"ℹ️ OpenALPR Local: Candidato encontrado -> {plate} (Confianza: {results[0].get('confidence', 0):.2f}%)")
            
        return {
            "vehicle": {
                "type": "",
                "score": 0.0,
                "color": ""
            },
            "plate": plate
        }
    except Exception as e:
        print(f"❌ Error en OpenALPR Local LPR: {e}")
        return None

def detectar_patente_snapshot_cloud(ruta_imagen):
    """Procesa la imagen usando Snapshot Cloud (Plate Recognizer) API y devuelve el formato estructurado estándar."""
    try:
        api_token = getattr(config, 'SNAPSHOT_CLOUD_API_TOKEN', '')
        if not api_token:
            print("❌ Error: SNAPSHOT_CLOUD_API_TOKEN no configurado en config.py")
            return None
            
        url = 'https://api.platerecognizer.com/v1/plate-reader/'
        headers = {'Authorization': f'Token {api_token}'}
        
        with open(ruta_imagen, 'rb') as img_file:
            response = requests.post(url, headers=headers, files={'upload': img_file}, timeout=15)
            
        if response.status_code not in (200, 201):
            print(f"❌ Error en Snapshot Cloud API (status {response.status_code}): {response.text}")
            return None
            
        data = response.json()
        results = data.get("results", [])
        
        plate = ""
        v_type = ""
        v_score = 0.0
        v_color = ""
        
        if results:
            first_res = results[0]
            plate = first_res.get("plate", "")
            vehicle_data = first_res.get("vehicle", {})
            
            v_type = vehicle_data.get("type", "")
            v_score = vehicle_data.get("score", 0.0)
            
            # Intentar extraer color
            v_color = vehicle_data.get("color", "")
            if not v_color:
                color_data = first_res.get("color", {})
                if isinstance(color_data, dict):
                    v_color = color_data.get("color", "")
                elif isinstance(color_data, list) and len(color_data) > 0:
                    v_color = color_data[0].get("color", "") if isinstance(color_data[0], dict) else ""
            
            print(f"ℹ️ Snapshot Cloud: Candidato encontrado -> {plate} | Tipo: {v_type} | Color: {v_color} | Confianza: {v_score:.3f}")
            
        return {
            "vehicle": {
                "type": v_type,
                "score": v_score,
                "color": v_color
            },
            "plate": plate
        }
    except Exception as e:
        print(f"❌ Error en Snapshot Cloud LPR: {e}")
        return None

METODOS_LPR = {
    'tesseract': detectar_patente_tesseract,
    'openalpr_local': detectar_patente_openalpr_local,
    'snapshot_cloud': detectar_patente_snapshot_cloud,
    'openalpr_cloud': detectar_patente_snapshot_cloud,  # Con redirección
}

def detectar_patente(ruta_imagen):
    """Procesa la imagen según el LPR_METHOD configurado y devuelve el diccionario estructurado o None."""
    try:
        method = getattr(config, 'LPR_METHOD', 'snapshot_cloud').lower()
        
        # Opcional: Redirección heredada de 'openalpr_cloud' a 'snapshot_cloud'
        if method == 'openalpr_cloud':
            print("ℹ️ Redirigiendo de 'openalpr_cloud' a 'snapshot_cloud' según la última configuración del sistema.")
            
        processor = METODOS_LPR.get(method, detectar_patente_tesseract)
        
        # Opcional: Loguear si se usó el fallback por un método no reconocido
        if method not in METODOS_LPR:
            print(f"⚠️ Método LPR no reconocido: '{method}'. Usando Tesseract por defecto.")
            
        resultado_crudo = processor(ruta_imagen)
        
        # 1. Evento de detección LPR (LPR_DETECTION)
        success = bool(resultado_crudo and resultado_crudo.get("plate"))
        lpr_payload = {
            "event": "LPR_DETECTION",
            "dsc": f"Imagen procesada con el metodo {processor}",
            "success": success,
            "result": resultado_crudo,
            "timestamp": datetime.now().isoformat()
        }
        mqtt_manager.publicar_mensaje(config.TOPIC_EVENTO, lpr_payload)


        if not resultado_crudo or not resultado_crudo.get("plate"):
            return None
            
        texto_crudo = resultado_crudo["plate"]
        
        # 1. Limpieza básica: quitar espacios, saltos de línea y caracteres no alfanuméricos
        texto_limpio = re.sub(r'[^A-Za-z0-9]', '', texto_crudo)
        
        # 2. Normalización de errores comunes de OCR
        texto_normalizado = normalizar_ocr(texto_limpio)
        
        # 3. Validación con Regex para formatos argentinos (Viejo y Mercosur)
        patron_patente = re.compile(r'^([A-Z]{3}\d{3}|[A-Z]{2}\d{3}[A-Z]{2})$')
        
        if patron_patente.match(texto_normalizado):
            print(f"✅ LPR ({method.upper()}): Patente detectada -> {texto_normalizado}")
            resultado_crudo["plate"] = texto_normalizado
            return resultado_crudo
        else:
            print(f"⚠️ LPR ({method.upper()}): Formato inválido o no reconocido. Crudo: '{texto_crudo.strip()}' | Normalizado: '{texto_normalizado}'")
            return None
            
    except Exception as e:
        print(f"❌ Error crítico en el módulo LPR: {e}")
        return None

if __name__ == "__main__":
    print("🧪 Probando módulo LPR para Argentina...")
    # Recuerda poner una imagen real de prueba en la carpeta
    resultado = detectar_patente("patente.png")
    print(f"Resultado final: {resultado}")
