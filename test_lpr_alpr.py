# test_lpr_alpr.py
import sys
import os
import config
import lpr_processor

def probar_metodo_lpr(metodo, ruta_imagen):
    print(f"\n--- Probando método: {metodo.upper()} ---")
    config.LPR_METHOD = metodo
    
    # Ejecutar detección
    resultado = lpr_processor.detectar_patente(ruta_imagen)
    print(f"Resultado para {metodo.upper()}: {resultado}")
    return resultado

if __name__ == "__main__":
    # 1. Determinar imagen a usar
    ruta_imagen = None
    if len(sys.argv) > 1:
        ruta_imagen = sys.argv[1]
    else:
        # Buscar en la carpeta imgs
        posibles_rutas = [
            "patente.png",
            os.path.join("imgs", "patente_01.jpg"),
            os.path.join("imgs", "patente_02.png"),
            os.path.join("imgs", "patente_03.png"),
            os.path.join("imgs", "patente_04.jpg")
        ]
        for ruta in posibles_rutas:
            if os.path.exists(ruta):
                ruta_imagen = ruta
                break

    if not ruta_imagen or not os.path.exists(ruta_imagen):
        print("❌ Error: No se encontró ninguna imagen de prueba.")
        print("Por favor, especifica una imagen: python test_lpr_alpr.py [ruta_imagen]")
        sys.exit(1)

    print(f"🧪 Iniciando comparación de motores LPR con la imagen: {ruta_imagen}")
    
    # 2. Ejecutar cada método
    resultados = {}
    
    # Tesseract
    resultados['tesseract'] = probar_metodo_lpr('tesseract', ruta_imagen)
    
    # OpenALPR Local
    # resultados['openalpr_local'] = probar_metodo_lpr('openalpr_local', ruta_imagen)
    
    # Snapshot Cloud (Plate Recognizer)
    if config.SNAPSHOT_CLOUD_API_TOKEN and "tu_token" not in config.SNAPSHOT_CLOUD_API_TOKEN and len(config.SNAPSHOT_CLOUD_API_TOKEN) > 20:
        resultados['snapshot_cloud'] = probar_metodo_lpr('snapshot_cloud', ruta_imagen)
    else:
        print("\n⚠️ Omitiendo Snapshot Cloud porque no se detectó un API Token válido en config.py.")
        resultados['snapshot_cloud'] = "No ejecutado (sin API Token)"

    # 3. Resumen final
    print("\n========================================")
    print("📊 RESUMEN DE RESULTADOS LPR")
    print("========================================")
    for metodo, res in resultados.items():
        print(f"- {metodo.upper()}: {res if res else 'Ninguno/No reconocido'}")
    print("========================================")
