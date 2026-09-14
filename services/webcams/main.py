import os
import sys
import json

import platform
import subprocess
import urllib.request
import zipfile
import stat
import time

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

# Añadir la raíz del proyecto al path para importar módulos compartidos (core)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

GO2RTC_VERSION = "v1.9.5"
GO2RTC_DIR = os.path.join(os.path.dirname(__file__), 'bin')
GO2RTC_EXE = os.path.join(GO2RTC_DIR, "go2rtc.exe" if sys.platform == "win32" else "go2rtc")

def download_go2rtc():
    """Descarga el ejecutable de go2rtc correspondiente al OS y Arquitectura."""
    if os.path.exists(GO2RTC_EXE):
        return

    print("⬇️ Ejecutable go2rtc no encontrado. Descargando...")
    os.makedirs(GO2RTC_DIR, exist_ok=True)
    
    os_name = platform.system().lower()
    arch = platform.machine().lower()
    
    if os_name == "windows":
        url = f"https://github.com/AlexxIT/go2rtc/releases/download/{GO2RTC_VERSION}/go2rtc_win64.zip"
        zip_path = os.path.join(GO2RTC_DIR, "go2rtc.zip")
        urllib.request.urlretrieve(url, zip_path)
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(GO2RTC_DIR)
        os.remove(zip_path)
    elif os_name == "linux":
        if "arm" in arch or "aarch" in arch:
            # Asumimos arm64/aarch64 (Raspberry Pi 4 64 bits)
            url = f"https://github.com/AlexxIT/go2rtc/releases/download/{GO2RTC_VERSION}/go2rtc_linux_arm64"
        else:
            url = f"https://github.com/AlexxIT/go2rtc/releases/download/{GO2RTC_VERSION}/go2rtc_linux_amd64"
        
        urllib.request.urlretrieve(url, GO2RTC_EXE)
        # Dar permisos de ejecución
        st = os.stat(GO2RTC_EXE)
        os.chmod(GO2RTC_EXE, st.st_mode | stat.S_IEXEC)
    else:
        print(f"❌ SO no soportado automáticamente: {os_name}")
        sys.exit(1)
        
    print(f"✅ go2rtc descargado en {GO2RTC_EXE}")

def generate_yaml():
    """Lee cameras.json y genera la configuración yaml de go2rtc."""
    config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../cameras.json'))
    
    if not os.path.exists(config_path):
        print(f"❌ Archivo no encontrado: {config_path}")
        print("Creando archivo de ejemplo...")
        ejemplo = {"cam_ejemplo": "rtsp://admin:admin@192.168.1.10/stream"}
        with open(config_path, 'w') as f:
            json.dump(ejemplo, f, indent=4)
        sys.exit(1)
        
    with open(config_path, 'r') as f:
        cameras = json.load(f)
        
    yaml_data = {
        "streams": cameras,
        "api": {
            "listen": ":1984" # Interfaz web de go2rtc
        },
        "webrtc": {
            "listen": ":8555" # Puerto para WebRTC
        }
    }
    
    yaml_path = os.path.join(GO2RTC_DIR, 'go2rtc_auto.yaml')
    with open(yaml_path, 'w') as f:
        # go2rtc soporta parsear JSON como YAML, evitamos requerir 'pyyaml'
        json.dump(yaml_data, f, indent=2)
        
    print(f"📄 Configuración YAML generada con {len(cameras)} cámaras.")
    return yaml_path

def run_go2rtc(yaml_path):
    """Inicia go2rtc como un subproceso y lo monitorea."""
    print("🚀 Iniciando servidor go2rtc...")
    
    cmd = [GO2RTC_EXE, "-config", yaml_path]
    try:
        process = subprocess.Popen(cmd)
        process.wait()
    except KeyboardInterrupt:
        print("\n🛑 Apagando servidor go2rtc...")
        process.terminate()
        process.wait()

if __name__ == "__main__":
    download_go2rtc()
    yaml_cfg = generate_yaml()
    run_go2rtc(yaml_cfg)
