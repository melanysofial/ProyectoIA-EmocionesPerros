#!/usr/bin/env python3
"""
Script de prueba para verificar que Telegram funcione correctamente
================================================================

Este script prueba la conectividad y funcionalidad básica del bot de Telegram
antes de ejecutar la aplicación principal.
"""

import logging
import sys
import time
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def test_telegram_connection():
    """Probar la conexión con Telegram usando la versión corregida"""
    
    print("\n" + "="*60)
    print("🧪 PRUEBA DE CONEXIÓN TELEGRAM - VERSION CORREGIDA")
    print("="*60)
    
    try:
        # Importar la versión corregida
        from utils.telegram_simple import SimpleTelegramBot
        
        # Configuración
        TOKEN = "7668982184:AAEXrM7xx0bDKidNOhyi6xjSNYUNRpvu61U"
        CHAT_ID = "1673887715"
        
        print(f"📱 Token: {TOKEN[:20]}...")
        print(f"💬 Chat ID: {CHAT_ID}")
        
        # Crear bot
        print("\n🔧 Creando bot...")
        bot = SimpleTelegramBot(TOKEN, CHAT_ID)
        print("✅ Bot creado exitosamente")
        
        # Test de conexión
        print("\n🧪 Probando conexión...")
        start_time = time.time()
        success = bot.test_connection()
        test_time = time.time() - start_time
        
        if success:
            print(f"✅ Conexión exitosa ({test_time:.2f}s)")
        else:
            print(f"❌ Conexión fallida ({test_time:.2f}s)")
            return False
        
        # Test de funciones adicionales
        print("\n🧪 Probando funciones adicionales...")
        
        # Test mensaje de bienvenida
        print("📝 Enviando mensaje de bienvenida...")
        welcome_success = bot.send_welcome_message()
        print(f"{'✅' if welcome_success else '❌'} Mensaje de bienvenida")
        
        # Test alerta
        print("🚨 Enviando alerta de prueba...")
        alert_success = bot.send_alert('happy', 0.95)
        print(f"{'✅' if alert_success else '❌'} Alerta de prueba")
        
        # Test resumen de video
        print("📹 Enviando resumen de video de prueba...")
        video_stats = {
            'video_name': 'test_video.mp4',
            'total_emotions': 10,
            'emotion_distribution': {'happy': 6, 'relaxed': 4},
            'dominant_emotion': 'happy',
            'confidence_avg': 0.85
        }
        video_success = bot.send_video_summary(video_stats)
        print(f"{'✅' if video_success else '❌'} Resumen de video")
        
        # Test actualización de historial
        print("📊 Actualizando historial...")
        for emotion in ['happy', 'relaxed', 'happy']:
            bot.update_emotion_history(emotion)
        print("✅ Historial actualizado")
        
        # Test limpieza
        print("🧹 Probando limpieza...")
        clear_success = bot.clear_chat_sync()
        print(f"{'✅' if clear_success else '❌'} Limpieza de chat")
        
        # Resumen final
        total_tests = 5
        passed_tests = sum([
            success, welcome_success, alert_success, 
            video_success, clear_success
        ])
        
        print(f"\n📊 RESUMEN: {passed_tests}/{total_tests} pruebas exitosas")
        
        if passed_tests == total_tests:
            print("🎉 TODAS LAS PRUEBAS EXITOSAS - Telegram funciona correctamente")
            return True
        elif passed_tests >= 3:
            print("⚠️ FUNCIONALIDAD PARCIAL - Telegram funciona con limitaciones")
            return True
        else:
            print("❌ FALLOS CRÍTICOS - Telegram no funciona correctamente")
            return False
        
    except ImportError as e:
        print(f"❌ Error importando módulos: {e}")
        return False
    except Exception as e:
        print(f"❌ Error en prueba: {e}")
        logger.exception("Detalles del error:")
        return False
    finally:
        print("="*60)

def test_app_integration():
    """Probar que la aplicación principal puede importar los módulos corregidos"""
    
    print("\n🔧 PRUEBA DE INTEGRACIÓN CON APP.PY")
    print("-"*40)
    
    try:
        # Probar importaciones
        print("📦 Probando importaciones...")
        
        from utils.telegram_simple import SimpleTelegramBot as TelegramBot
        print("✅ telegram_simple importado")
        
        from utils.cam_utils import EmotionDetector
        print("✅ cam_utils importado")
        
        from utils.yolo_dog_detector import YoloDogDetector
        print("✅ yolo_dog_detector importado")
        
        # Probar creación de bot
        print("\n🤖 Probando creación de bot...")
        TOKEN = "7668982184:AAEXrM7xx0bDKidNOhyi6xjSNYUNRpvu61U"
        CHAT_ID = "1673887715"
        
        bot = TelegramBot(TOKEN, CHAT_ID)
        print("✅ Bot creado sin errores")
        
        # Probar métodos requeridos por app.py
        print("\n🔍 Verificando métodos requeridos...")
        methods_to_check = [
            'test_connection',
            'send_welcome_message', 
            'send_alert',
            'send_video_summary',
            'send_simple_message',
            'update_emotion_history',
            'send_periodic_update',
            'clear_chat_sync',
            'cleanup'
        ]
        
        missing_methods = []
        for method in methods_to_check:
            if hasattr(bot, method):
                print(f"✅ {method}")
            else:
                print(f"❌ {method} - FALTANTE")
                missing_methods.append(method)
        
        if not missing_methods:
            print("\n🎉 INTEGRACIÓN EXITOSA - Todos los métodos disponibles")
            return True
        else:
            print(f"\n❌ MÉTODOS FALTANTES: {missing_methods}")
            return False
        
    except Exception as e:
        print(f"❌ Error en integración: {e}")
        logger.exception("Detalles del error:")
        return False

def main():
    """Ejecutar todas las pruebas"""
    
    print(f"🐕 DOG EMOTION AI - PRUEBA DE TELEGRAM")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Ejecutar pruebas
    telegram_ok = test_telegram_connection()
    integration_ok = test_app_integration()
    
    # Resumen final
    print(f"\n{'='*60}")
    print("📋 RESUMEN FINAL")
    print(f"{'='*60}")
    print(f"🔗 Conexión Telegram: {'✅ OK' if telegram_ok else '❌ FALLO'}")
    print(f"🔧 Integración App: {'✅ OK' if integration_ok else '❌ FALLO'}")
    
    if telegram_ok and integration_ok:
        print(f"\n🎉 TODAS LAS PRUEBAS EXITOSAS")
        print(f"✅ La aplicación debería funcionar correctamente con Telegram")
        print(f"🚀 Puedes ejecutar 'python main.py' con confianza")
        return True
    else:
        print(f"\n❌ HAY PROBLEMAS QUE CORREGIR")
        print(f"🔧 Revisa los errores arriba antes de ejecutar la aplicación")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n👋 Prueba interrumpida por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Error crítico: {e}")
        logger.exception("Traceback completo:")
        sys.exit(2)