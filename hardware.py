# hardware.py
import time
import config

try:
    from gpiozero import MotionSensor, OutputDevice
    pir = MotionSensor(config.PIN_PIR)
    rele_porton = OutputDevice(config.PIN_RELE, active_high=False)
    HAS_GPIO = True
except (ImportError, OSError) as e:
    print(f"⚠️ Advertencia: GPIO no disponible ({e}). Ejecutando en modo simulación.")
    HAS_GPIO = False
    pir = None
    rele_porton = None

def abrir_porton():
    print("✅ Abriendo portón...")
    if HAS_GPIO and rele_porton:
        rele_porton.on()
        time.sleep(config.TIEMPO_ACTIVACION_RELE)
        rele_porton.off()
    else:
        time.sleep(config.TIEMPO_ACTIVACION_RELE)
        print("🚪 [Simulado] El portón se abrió y se cerró de forma segura.")

def esperar_movimiento():
    if HAS_GPIO and pir:
        pir.wait_for_motion()
    else:
        # En modo simulación, para no congelar indefinidamente
        time.sleep(10)
        print("🚨 [Simulado] Se detectó movimiento en el sensor PIR.")

def esperar_sin_movimiento():
    if HAS_GPIO and pir:
        pir.wait_for_no_motion()
    else:
        time.sleep(2)
        print("💤 [Simulado] El sensor PIR reporta fin de movimiento.")
