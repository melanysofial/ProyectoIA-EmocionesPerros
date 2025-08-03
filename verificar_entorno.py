#!/usr/bin/env python3
"""
Script de verificación del entorno
Comprueba que todo esté configurado correctamente antes de ejecutar el sistema principal
"""

import sys
import os
from pathlib import Path

def check_python_version():
    """Verificar versión de Python"""
    print("🐍 Verificando Python...")
    if sys.version_info < (3, 8):
        print(f"❌ Python {sys.version_info.major}.{sys.version_info.minor} no es compatible")
        print("   Requiere Python 3.8 o superior")
        return False
    else:
        print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro} - Compatible")
        return True

def check_dependencies():
    """Verificar dependencias instaladas"""
    print("\n📦 Verificando dependencias...")
    
    required_packages = [
        'cv2', 'numpy', 'tensorflow', 'ultralytics', 'requests', 'PIL'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'cv2':
                import cv2
            elif package == 'numpy':
                import numpy
            elif package == 'tensorflow':
                import tensorflow
            elif package == 'ultralytics':
                import ultralytics
            elif package == 'requests':
                import requests
            elif package == 'PIL':
                from PIL import Image
            print(f"✅ {package} - Instalado")
        except ImportError:
            print(f"❌ {package} - NO instalado")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️ Paquetes faltantes: {', '.join(missing_packages)}")
        print("Ejecuta: pip install -r requirements.txt")
        return False
    
    return True

def check_project_structure():
    """Verificar estructura del proyecto"""
    print("\n📁 Verificando estructura del proyecto...")
    
    project_root = Path(__file__).parent
    
    required_files = [
        "main.py",
        "config.py",
        "requirements.txt",
        "modelo/mejor_modelo_83.h5",
        "utils/cam_utils.py",
        "utils/telegram_utils.py",
        "utils/yolo_dog_detector.py"
    ]
    
    missing_files = []
    
    for file_path in required_files:
        full_path = project_root / file_path
        if full_path.exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - NO encontrado")
            missing_files.append(file_path)
    
    if missing_files:
        print(f"\n⚠️ Archivos faltantes: {', '.join(missing_files)}")
        return False
    
    return True

def check_config():
    """Verificar configuración"""
    print("\n⚙️ Verificando configuración...")
    
    try:
        from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID
        
        if TELEGRAM_TOKEN.startswith("7668982184:"):
            print("✅ Token de Telegram configurado correctamente")
        else:
            print("❌ Token de Telegram incorrecto")
            return False
        
        if TELEGRAM_CHAT_ID == "1673887715":
            print("⚠️ Usando Chat ID por defecto - Configura el tuyo en config.py")
        else:
            print(f"✅ Chat ID personalizado configurado: {TELEGRAM_CHAT_ID}")
        
        return True
        
    except ImportError:
        print("❌ Archivo config.py no encontrado o configuración incorrecta")
        return False

def check_camera():
    """Verificar cámara disponible"""
    print("\n📹 Verificando cámara...")
    
    try:
        import cv2
        
        # Probar cámaras del 0 al 2
        for i in range(3):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret and frame is not None:
                    print(f"✅ Cámara {i} disponible: {frame.shape[1]}x{frame.shape[0]}")
                    cap.release()
                    return True
                cap.release()
        
        print("❌ No se encontró ninguna cámara disponible")
        print("   Asegúrate de que tu cámara esté conectada y no esté siendo usada por otra aplicación")
        return False
        
    except Exception as e:
        print(f"❌ Error verificando cámara: {e}")
        return False

def main():
    """Función principal de verificación"""
    print("🔍 VERIFICACIÓN DEL ENTORNO - Monitor de Emociones Caninas")
    print("=" * 60)
    
    checks = [
        ("Python", check_python_version),
        ("Dependencias", check_dependencies),
        ("Estructura", check_project_structure),
        ("Configuración", check_config),
        ("Cámara", check_camera)
    ]
    
    all_passed = True
    
    for check_name, check_func in checks:
        try:
            if not check_func():
                all_passed = False
        except Exception as e:
            print(f"❌ Error en verificación de {check_name}: {e}")
            all_passed = False
    
    print("\n" + "=" * 60)
    
    if all_passed:
        print("🎉 ¡VERIFICACIÓN COMPLETADA EXITOSAMENTE!")
        print("✅ Tu sistema está listo para ejecutar el Monitor de Emociones Caninas")
        print("\n📋 Próximos pasos:")
        print("   1. Ejecuta: python main.py")
        print("   2. O usa el archivo ejecutar.bat")
        print("   3. Configura tu Chat ID en config.py si no lo has hecho")
    else:
        print("❌ VERIFICACIÓN FALLÓ")
        print("⚠️ Soluciona los problemas mostrados arriba antes de continuar")
        print("\n🔧 Soluciones comunes:")
        print("   - Instalar dependencias: pip install -r requirements.txt")
        print("   - Verificar que todos los archivos estén presentes")
        print("   - Configurar Chat ID en config.py")
        print("   - Conectar cámara y dar permisos")
    
    print("\n📚 Para más ayuda, consulta el README.md")
    
    # Mantener ventana abierta
    input("\nPresiona Enter para salir...")

if __name__ == "__main__":
    main()
