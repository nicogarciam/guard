# plate_validator.py
import config
import storage
import mqtt_manager
from datetime import datetime

def validar_patente_local(resultado_lpr):
    """Valida la patente contra la base de datos local de patentes autorizadas."""
    if not resultado_lpr:
        return False
        
    if isinstance(resultado_lpr, dict):
        patente = resultado_lpr.get("plate")
    else:
        patente = resultado_lpr
        
    if not patente:
        return False
        
    patentes_autorizadas = storage.cargar_patentes_locales()
    return patente in patentes_autorizadas

VALIDADORES = {
    'local': validar_patente_local,
    # 'remoto': validar_patente_remota,  # Ejemplo para futuro
    # 'api': validar_patente_por_api,    # Ejemplo para futuro
}

def validar_patente(resultado_lpr):
    """
    Valida la patente utilizando el método configurado.
    Recibe el JSON/dict completo retornado por el procesador LPR.
    """
    metodo = getattr(config, 'VALIDATION_METHOD', 'local').lower()
    
    # Obtener el validador del factory. 
    # Si el método no existe, hacemos fallback a 'local' de forma segura.
    validator = VALIDADORES.get(metodo, validar_patente_local)
    
    # Opcional: Loguear si se usó el fallback por un método no reconocido
    if metodo not in VALIDADORES:
        print(f"⚠️ Método de validación '{metodo}' no reconocido. Usando validación local por defecto.")

    # 3. Ejecutar el validador seleccionado pasándole el objeto completo
    result = validator(resultado_lpr)

    # Extraer la patente para construir el payload del evento
    if isinstance(resultado_lpr, dict):
        patente = resultado_lpr.get("plate")
    else:
        patente = resultado_lpr

    # 4. Construir y publicar el evento (Responsabilidad separada de la validación)
    validation_payload = {
        "event": "PLATE_VALIDATION",
        "dsc": f"Imagen validada con el metodo {processor}",
        "plate": patente,
        "authorized": result,
        "timestamp": datetime.now().isoformat()
    }
    
    print(f"📡 Publicando evento PLATE_VALIDATION por MQTT... Autorizado: {result}")
    mqtt_manager.publicar_mensaje(config.TOPIC_EVENTO, validation_payload)
    
    return result

