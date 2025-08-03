#!/usr/bin/env python3
"""
Ejemplo completo de uso del procesador de video con Telegram
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

# Importar configuración
try:
    from config import *
    print("✅ Configuración cargada desde config.py")
except ImportError:
    print("⚠️ Archivo config.py no encontrado, usando configuración por defecto")

from procesar_video import process_video

def main():
    """Ejemplo de procesamiento con notificación por Telegram"""
    
    print("🎬 DEMO: Procesador de Video con Telegram")
    print("=" * 50)
    
    # Usar uno de los videos de ejemplo
    video_paths = [
        "media/videoprueba1.mp4",
        "media/videoprueba2.mp4",
        "videoprueba1_procesado.mp4",
        "videoprueba2_procesado.mp4"
    ]
    
    # Buscar un video disponible
    video_to_process = None
    for video_path in video_paths:
        if os.path.exists(video_path):
            video_to_process = video_path
            break
    
    if not video_to_process:
        print("❌ No se encontraron videos de ejemplo")
        print("📁 Videos buscados:")
        for path in video_paths:
            print(f"   - {path}")
        print("\nColoca un video en la carpeta 'media/' y vuelve a intentar")
        return
    
    print(f"✅ Video encontrado: {video_to_process}")
    print("🚀 Iniciando procesamiento con notificación por Telegram...")
    print("📱 Al terminar recibirás un resumen completo en Telegram")
    print()
    
    # Procesar video con todas las opciones
    stats = process_video(
        video_path=video_to_process,
        output_path=None,  # Generar automáticamente
        show_video=True,   # Mostrar durante procesamiento
        save_video=True    # Guardar resultado
    )
    
    if stats:
        print("\n🎉 ¡Procesamiento completado!")
        print("📱 Revisa tu Telegram para ver el resumen detallado")
    else:
        print("\n❌ Error durante el procesamiento")

if __name__ == "__main__":
    main()
