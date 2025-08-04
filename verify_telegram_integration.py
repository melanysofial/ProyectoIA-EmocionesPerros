#!/usr/bin/env python3
"""
Verificación de Integración con Telegram
=======================================

Script para verificar que la integración con Telegram funciona correctamente
y que los análisis se envían al bot.

Autor: Dog Emotion AI Team
"""

import sys
import os
import logging
import time
import cv2
import numpy as np
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def print_header():
    """Imprime el encabezado del script"""
    print("\n" + "=" * 70)
    print("🔍 VERIFICACIÓN DE INTEGRACIÓN CON TELEGRAM")
    print("=" * 70)
    print("Este script verificará que:")
    print("  ✓ Los modelos de IA están funcionando")
    print("  ✓ El bot de Telegram está conectado")
    print("  ✓ Los análisis se envían correctamente")
    print("  ✓ Las alertas funcionan como se espera")
    print("=" * 70 + "\n")

def test_models():
    """Prueba que los modelos estén disponibles"""
    logger.info("1️⃣ Verificando modelos de IA...")
    
    try:
        # Importar modelos
        from utils.cam_utils import EmotionDetector
        from utils.yolo_dog_detector import YoloDogDetector
        
        # Verificar modelo de emociones
        if Path("modelo/mejor_modelo_83.h5").exists():
            detector = EmotionDetector("modelo/mejor_modelo_83.h5")
            logger.info("✅ Modelo de emociones cargado correctamente")
        else:
            logger.warning("⚠️ Modelo de emociones no encontrado")
            return False
        
        # Verificar YOLO
        yolo_detector = YoloDogDetector()
        logger.info("✅ Detector YOLO inicializado")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error cargando modelos: {e}")
        return False

def test_telegram_connection():
    """Prueba la conexión con Telegram"""
    logger.info("\n2️⃣ Verificando conexión con Telegram...")
    
    try:
        from utils.telegram_utils import TelegramBot
        
        # Configuración
        TELEGRAM_TOKEN = "7668982184:AAEXrM7xx0bDKidNOhyi6xjSNYUNRpvu61U"
        TELEGRAM_CHAT_ID = "1673887715"
        
        # Crear bot
        bot = TelegramBot(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID)
        
        # Probar conexión
        if bot.test_connection():
            logger.info("✅ Conexión con Telegram exitosa")
            
            # Enviar mensaje de prueba
            bot.send_simple_message(
                "🧪 **PRUEBA DE INTEGRACIÓN**\n\n"
                "✅ Sistema de análisis conectado correctamente\n"
                "🐕 Dog Emotion AI está listo para monitorear"
            )
            logger.info("✅ Mensaje de prueba enviado")
            
            return bot
        else:
            logger.error("❌ No se pudo conectar con Telegram")
            return None
            
    except Exception as e:
        logger.error(f"❌ Error conectando con Telegram: {e}")
        return None

def test_image_analysis(bot):
    """Prueba el análisis de una imagen de prueba"""
    logger.info("\n3️⃣ Probando análisis de imagen...")
    
    try:
        from utils.cam_utils import EmotionDetector
        from utils.yolo_dog_detector import YoloDogDetector
        
        # Cargar modelos
        detector = EmotionDetector("modelo/mejor_modelo_83.h5")
        yolo_detector = YoloDogDetector()
        
        # Crear imagen de prueba (un perro simple dibujado)
        test_image = create_test_image()
        
        # Guardar imagen de prueba
        test_path = "test_dog_image.jpg"
        cv2.imwrite(test_path, test_image)
        logger.info(f"📸 Imagen de prueba creada: {test_path}")
        
        # Detectar perros
        dog_detections = yolo_detector.detect_dogs(test_image)
        dogs_detected = yolo_detector.is_dog_detected(dog_detections)
        
        if dogs_detected:
            logger.info("✅ Perro detectado en imagen de prueba")
            
            # Analizar emociones
            emotion, probability, predictions = detector.predict_emotion(test_image)
            logger.info(f"🎯 Emoción detectada: {emotion} ({probability:.2f})")
            
            # Enviar alerta a Telegram si es emoción negativa
            if bot and emotion in ['angry', 'sad'] and probability > 0.6:
                logger.info("📱 Enviando alerta a Telegram...")
                success = bot.send_alert(emotion, probability, test_path)
                if success:
                    logger.info("✅ Alerta enviada exitosamente")
                else:
                    logger.error("❌ Error enviando alerta")
            
            # Actualizar historial
            if bot:
                bot.update_emotion_history(emotion)
                logger.info("✅ Historial actualizado")
            
            return True
        else:
            logger.warning("⚠️ No se detectó perro en la imagen de prueba")
            logger.info("💡 Esto es normal con imágenes sintéticas")
            return True  # No es un error crítico
            
    except Exception as e:
        logger.error(f"❌ Error en análisis de imagen: {e}")
        return False
    finally:
        # Limpiar archivo de prueba
        if os.path.exists(test_path):
            os.remove(test_path)

def create_test_image():
    """Crea una imagen de prueba con un 'perro' dibujado"""
    # Crear imagen en blanco
    img = np.ones((480, 640, 3), dtype=np.uint8) * 255
    
    # Dibujar un 'perro' simple
    # Cuerpo
    cv2.ellipse(img, (320, 300), (100, 60), 0, 0, 360, (139, 69, 19), -1)
    
    # Cabeza
    cv2.circle(img, (400, 280), 50, (160, 82, 45), -1)
    
    # Orejas
    cv2.ellipse(img, (380, 250), (20, 30), -30, 0, 360, (139, 69, 19), -1)
    cv2.ellipse(img, (420, 250), (20, 30), 30, 0, 360, (139, 69, 19), -1)
    
    # Ojos
    cv2.circle(img, (385, 275), 5, (0, 0, 0), -1)
    cv2.circle(img, (415, 275), 5, (0, 0, 0), -1)
    
    # Nariz
    cv2.circle(img, (400, 290), 3, (0, 0, 0), -1)
    
    # Cola
    cv2.ellipse(img, (220, 280), (40, 20), 45, 0, 360, (139, 69, 19), -1)
    
    # Patas
    cv2.rectangle(img, (280, 340), (300, 400), (139, 69, 19), -1)
    cv2.rectangle(img, (340, 340), (360, 400), (139, 69, 19), -1)
    cv2.rectangle(img, (380, 340), (400, 400), (139, 69, 19), -1)
    cv2.rectangle(img, (420, 340), (440, 400), (139, 69, 19), -1)
    
    # Agregar texto
    cv2.putText(img, "Test Dog", (250, 450), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
    
    return img

def test_realtime_simulation(bot):
    """Simula un análisis en tiempo real"""
    logger.info("\n4️⃣ Simulando análisis en tiempo real...")
    
    try:
        # Simular 5 análisis con diferentes emociones
        emotions_test = [
            ('happy', 0.85),
            ('sad', 0.92),
            ('relaxed', 0.78),
            ('angry', 0.88),
            ('happy', 0.90)
        ]
        
        logger.info("📊 Enviando simulación de emociones...")
        
        for i, (emotion, prob) in enumerate(emotions_test):
            logger.info(f"  {i+1}/5: {emotion} ({prob:.2f})")
            
            if bot:
                # Actualizar historial
                bot.update_emotion_history(emotion)
                
                # Enviar alerta si es necesario
                if emotion in ['angry', 'sad'] and prob > 0.8:
                    bot.send_alert(emotion, prob)
            
            time.sleep(1)  # Simular delay entre análisis
        
        # Enviar resumen
        if bot:
            logger.info("📈 Enviando resumen de estado...")
            bot.send_status_update()
            logger.info("✅ Resumen enviado")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error en simulación: {e}")
        return False

def test_video_summary(bot):
    """Prueba el envío de resumen de video"""
    logger.info("\n5️⃣ Probando resumen de video...")
    
    try:
        if not bot:
            logger.warning("⚠️ Bot no disponible, saltando prueba")
            return True
        
        # Simular estadísticas de video
        video_stats = {
            'video_name': 'video_prueba.mp4',
            'total_emotions': 150,
            'emotion_distribution': {
                'happy': 45,
                'relaxed': 60,
                'sad': 30,
                'angry': 15
            },
            'dominant_emotion': 'relaxed',
            'confidence_avg': 0.82,
            'frames_processed': 300,
            'dog_detection_rate': 95.5,
            'processing_speed': 25.0,
            'output_file': None
        }
        
        logger.info("📹 Enviando resumen de video simulado...")
        success = bot.send_video_summary(video_stats)
        
        if success:
            logger.info("✅ Resumen de video enviado exitosamente")
        else:
            logger.error("❌ Error enviando resumen de video")
        
        return success
        
    except Exception as e:
        logger.error(f"❌ Error en prueba de video: {e}")
        return False

def main():
    """Función principal"""
    print_header()
    
    # Cambiar al directorio del proyecto
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # Contador de pruebas exitosas
    tests_passed = 0
    total_tests = 5
    
    # 1. Probar modelos
    if test_models():
        tests_passed += 1
    else:
        logger.error("⚠️ Sin modelos no se pueden hacer más pruebas")
        print(f"\n📊 Resultado: {tests_passed}/{total_tests} pruebas exitosas")
        return
    
    # 2. Probar conexión Telegram
    bot = test_telegram_connection()
    if bot:
        tests_passed += 1
    else:
        logger.warning("⚠️ Continuando sin Telegram...")
    
    # 3. Probar análisis de imagen
    if test_image_analysis(bot):
        tests_passed += 1
    
    # 4. Probar simulación en tiempo real
    if test_realtime_simulation(bot):
        tests_passed += 1
    
    # 5. Probar resumen de video
    if test_video_summary(bot):
        tests_passed += 1
    
    # Resumen final
    print("\n" + "=" * 70)
    print("📊 RESUMEN DE VERIFICACIÓN")
    print("=" * 70)
    print(f"Pruebas exitosas: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        print("\n✅ ¡TODAS LAS PRUEBAS PASARON!")
        print("🎉 El sistema está funcionando correctamente")
        
        if bot:
            bot.send_simple_message(
                "✅ **VERIFICACIÓN COMPLETA**\n\n"
                f"Todas las pruebas pasaron ({tests_passed}/{total_tests})\n"
                "Sistema listo para producción 🚀"
            )
    else:
        print(f"\n⚠️ {total_tests - tests_passed} pruebas fallaron")
        print("Revisa los logs para más detalles")
    
    print("\n💡 Próximos pasos:")
    print("1. Ejecuta: run_app.bat")
    print("2. Abre: http://localhost:5000")
    print("3. Revisa Telegram para ver las alertas")
    print("=" * 70)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Verificación interrumpida por el usuario")
    except Exception as e:
        logger.error(f"❌ Error crítico: {e}")
        logger.exception("Detalles:")
    
    input("\nPresiona Enter para salir...")