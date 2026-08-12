# test_camara.py
import cv2
import time
import config

def probar_camara():
    index = getattr(config, 'CAMARA_INDEX', 0)
    print(f"📷 Intentando abrir cámara en índice {index}...")
    
    cap = cv2.VideoCapture(index)
    if not cap.isOpened():
        print(f"❌ Error: No se pudo acceder al dispositivo de cámara en el índice {index}.")
        print("💡 Sugerencia: Si usás cámara USB o V4L2, probá cambiar CAMARA_INDEX en config.py (0, 1, 2...).")
        return False
        
    print("⏳ Ajustando exposición y capturando cuadro...")
    time.sleep(1)
    
    ret, frame = cap.read()
    cap.release()
    
    if not ret or frame is None:
        print("❌ Error: El dispositivo respondió pero no entregó una imagen válida.")
        return False
        
    output_filename = "test_foto.jpg"
    cv2.imwrite(output_filename, frame)
    alto, ancho, canales = frame.shape
    print(f"✅ ¡Captura EXITOSA! Foto guardada como '{output_filename}' ({ancho}x{alto} px).")
    return True

if __name__ == "__main__":
    probar_camara()
