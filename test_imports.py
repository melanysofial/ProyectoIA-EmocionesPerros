#!/usr/bin/env python3
"""Script de prueba de importaciones"""

import sys
print(f"Python: {sys.version}")
print(f"Ejecutable: {sys.executable}")
print("-" * 50)

packages = [
    ("cv2", "OpenCV"),
    ("PIL", "Pillow"),
    ("flask", "Flask"),
    ("tensorflow", "TensorFlow"),
    ("numpy", "NumPy"),
    ("telegram", "python-telegram-bot"),
    ("ultralytics", "Ultralytics")
]

for module_name, display_name in packages:
    try:
        module = __import__(module_name)
        version = getattr(module, "__version__", "Unknown")
        print(f"✅ {display_name}: {version}")
    except ImportError as e:
        print(f"❌ {display_name}: Error - {e}")

print("-" * 50)
input("Presiona Enter para continuar...")
