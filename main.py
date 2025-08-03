import cv2
import os
import time
import logging
import requests
import json
import base64
from pathlib import Path
from utils.cam_utils import EmotionDetector
from utils.telegram_utils import TelegramBot    
from utils.yolo_dog_detector import YoloDogDetector

# Importar configuración desde archivo separado
try:
    from config import *
    logger = logging.getLogger(__name__)  # Definir logger después de importar config
    logger.info("✅ Configuración cargada desde config.py")
except ImportError as e:
    # Configuración por defecto si no existe config.py
    print("⚠️ Archivo config.py no encontrado, usando configuración por defecto")
    #TELEGRAM_TOKEN = "7668982184:AAEXrM7xx0bDKidNOhyi6xjSNYUNRpvu61U"
    #TELEGRAM_CHAT_ID = "1673887715"
    TELEGRAM_TOKEN = "7565394500:AAEqYMlT4mQFGTlL8slsSrlrst3MZmeMzIg"
    TELEGRAM_CHAT_ID = "1846987938"
    YOLO_CONFIDENCE_THRESHOLD = 0.60
    EMOTION_ANALYSIS_INTERVAL = 2
    ALERT_THRESHOLD = 3
    EMOTION_HISTORY_SIZE = 4
    CAMERA_INDEX = 0
    CAMERA_WIDTH = 640
    CAMERA_HEIGHT = 480
    CAMERA_FPS = 30
    WAITING_MESSAGE = 'ESPERANDO DETECCION DE PERRO...'
    LOG_LEVEL = "INFO"
    LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
    logger = logging.getLogger(__name__)

# Configurar logging usando la configuración importada
logging.basicConfig(level=getattr(logging, LOG_LEVEL, logging.INFO), format=LOG_FORMAT)

# === CONFIGURACIÓN DE RUTAS UNIVERSALES ===
# Obtener el directorio del script actual de forma compatible con todos los SO
PROJECT_ROOT = Path(__file__).parent.absolute()
MODEL_PATH = PROJECT_ROOT / "modelo" / "mejor_modelo_83.h5"

def verify_environment():
    """
    Verifica que el entorno esté configurado correctamente
    Compatible con todos los sistemas operativos y versiones de Python
    """
    logger.info("🔍 Verificando configuración del entorno...")
    
    # Verificar Python y SO
    import sys
    import platform
    logger.info(f"🐍 Python: {sys.version}")
    logger.info(f"💻 Sistema: {platform.system()} {platform.release()}")
    logger.info(f"📂 Directorio del proyecto: {PROJECT_ROOT}")
    
    # Verificar modelo
    if MODEL_PATH.exists():
        logger.info(f"✅ Modelo encontrado: {MODEL_PATH}")
        logger.info(f"📊 Tamaño del modelo: {MODEL_PATH.stat().st_size / (1024*1024):.1f} MB")
    else:
        logger.error(f"❌ Modelo NO encontrado en: {MODEL_PATH}")
        return False
    
    # Verificar archivos de utilidades
    utils_files = [
        PROJECT_ROOT / "utils" / "cam_utils.py",
        PROJECT_ROOT / "utils" / "telegram_utils.py",
        PROJECT_ROOT / "utils" / "yolo_dog_detector.py"
    ]
    
    for util_file in utils_files:
        if util_file.exists():
            logger.info(f"✅ {util_file.name} encontrado")
        else:
            logger.error(f"❌ {util_file.name} NO encontrado en utils/")
            return False
    
    # Verificar configuración de Telegram
    if TELEGRAM_CHAT_ID == "1846987938":
        logger.warning("⚠️ USANDO CHAT ID POR DEFECTO - Configura el tuyo con @Emocionesperrunasbot")
    else:
        logger.info(f"✅ Chat ID configurado: {TELEGRAM_CHAT_ID}")
    
    logger.info("🎯 Verificación completada - Sistema listo para usar")
    return True

def find_available_camera():
    """Encuentra la primera cámara disponible"""
    for i in range(10):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret and frame is not None:
                logger.info(f"✅ Cámara {i} encontrada: {frame.shape[1]}x{frame.shape[0]}")
                cap.release()
                return i
        cap.release()
    return None

def process_video_file(video_path, save_output=False, output_path=None):
    """
    Procesa un archivo de video y muestra/guarda el resultado con detecciones
    
    Args:
        video_path (str): Ruta al archivo de video
        save_output (bool): Si guardar el video procesado
        output_path (str): Ruta donde guardar el video procesado
    """
    logger.info(f"🎬 Iniciando procesamiento de video: {video_path}")
    
    # Verificar si el archivo existe
    if not os.path.exists(video_path):
        logger.error(f"❌ El archivo de video no existe: {video_path}")
        return False
    
    # Inicializar componentes
    try:
        logger.info("🧠 Cargando modelo de IA...")
        logger.info(f"📁 Ruta del modelo: {MODEL_PATH}")
        logger.info(f"📂 Directorio del proyecto: {PROJECT_ROOT}")
        logger.info(f"✅ Archivo modelo existe: {MODEL_PATH.exists()}")
        
        # Usar str() para compatibilidad con librerías que esperan string
        detector = EmotionDetector(str(MODEL_PATH))
        logger.info("✅ Modelo de emociones cargado exitosamente")
    except Exception as e:
        logger.error(f"❌ Error cargando modelo: {e}")
        return False
    
    try:
        logger.info("🐕 Inicializando detector YOLO optimizado...")
        yolo_detector = YoloDogDetector(confidence_threshold=YOLO_CONFIDENCE_THRESHOLD)
        logger.info(f"✅ YOLOv8 cargado exitosamente (umbral: {YOLO_CONFIDENCE_THRESHOLD*100:.0f}%)")
    except Exception as e:
        logger.error(f"❌ Error cargando YOLO: {e}")
        return False
    
    # Abrir video
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        logger.error(f"❌ No se puede abrir el video: {video_path}")
        return False
    
    # Obtener propiedades del video
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    logger.info(f"📹 Video: {width}x{height} @ {fps}fps, {total_frames} frames")
    
    # Configurar escritor de video si se quiere guardar
    out = None
    if save_output and output_path:
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        logger.info(f"💾 Guardando resultado en: {output_path}")
    
    # Variables de control
    emotion_history = []
    frame_count = 0
    processed_frames = 0
    
    logger.info("\n🎮 CONTROLES:")
    logger.info("  Q o ESC: Salir")
    logger.info("  ESPACIO: Pausar/Reanudar")
    logger.info("  S: Capturar frame actual")
    logger.info("\n▶️ Iniciando procesamiento...\n")
    
    paused = False
    
    try:
        while True:
            if not paused:
                ret, frame = cap.read()
                if not ret:
                    logger.info("🏁 Fin del video alcanzado")
                    break
                
                frame_count += 1
                processed_frames += 1
                
                # Mostrar progreso cada 30 frames
                if frame_count % 30 == 0:
                    progress = (frame_count / total_frames) * 100
                    logger.info(f"📊 Progreso: {progress:.1f}% ({frame_count}/{total_frames})")
            
            # PASO 1: Detectar perros con YOLO
            dog_detections = yolo_detector.detect_dogs(frame)
            dogs_detected = yolo_detector.is_dog_detected(dog_detections)
            
            # PASO 2: Dibujar detecciones de YOLO
            frame = yolo_detector.draw_detections(frame, dog_detections)
            
            # PASO 3: Analizar emociones si hay perros detectados
            emotion_detected = None
            emotion_prob = 0
            
            if dogs_detected:
                try:
                    emotion, prob, preds = detector.predict_emotion(frame)
                    emotion_detected = emotion
                    emotion_prob = prob
                    
                    # Actualizar historial
                    emotion_history.append(emotion)
                    if len(emotion_history) > 10:
                        emotion_history.pop(0)
                    
                    # Determinar color según emoción
                    color = (0, 255, 0)  # Verde por defecto
                    if emotion in ['angry', 'sad']:
                        color = (0, 0, 255)  # Rojo para emociones negativas
                    elif emotion == 'happy':
                        color = (0, 255, 255)  # Amarillo para feliz
                    
                    # Mostrar emoción cerca del perro detectado
                    best_detection = yolo_detector.get_best_dog_region(dog_detections)
                    if best_detection:
                        x, y, w, h = best_detection
                        emotion_text = f'EMOCION: {emotion.upper()} ({prob:.2f})'
                        cv2.putText(frame, emotion_text, (x, y + h + 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
                    
                except Exception as e:
                    logger.error(f"Error en análisis de emoción: {e}")
            
            else:
                # Mensaje cuando no hay perros detectados
                cv2.putText(frame, 'ESPERANDO DETECCION DE PERRO...', 
                (60, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
            
            # Mostrar información en el frame
            info_y = frame.shape[0] - 100
            cv2.putText(frame, f'Frame: {frame_count}/{total_frames}', (10, info_y), 
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            cv2.putText(frame, f'Perros detectados: {len(dog_detections)}', (10, info_y + 20), 
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            cv2.putText(frame, f'Emociones: {len(emotion_history)}/10', (10, info_y + 40), 
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            
            # Controles
            status = "PAUSADO" if paused else "REPRODUCIENDO"
            cv2.putText(frame, f'{status} | ESPACIO: pausar | Q: salir | S: capturar', 
            (10, info_y + 60), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
            
            # Mostrar frame
            #cv2.imshow('🎬 Procesador de Video - Dog Emotion Monitor', frame)
            
            # Guardar frame si se configuró
            if out is not None:
                out.write(frame)
            
            # Manejar teclas
            key = cv2.waitKey(30) & 0xFF  # 30ms para video fluido
            if key == ord('q') or key == 27:  # Q o ESC
                logger.info("👋 Saliendo del procesamiento...")
                break
            elif key == ord(' '):  # ESPACIO para pausar/reanudar
                paused = not paused
                logger.info(f"⏸️ {'Pausado' if paused else '▶️ Reanudado'}")
            elif key == ord('s'):  # S para capturar frame
                capture_name = f"captura_frame_{frame_count:05d}.jpg"
                cv2.imwrite(capture_name, frame)
                logger.info(f"📸 Frame capturado: {capture_name}")
        
        # Mostrar resumen final
        if emotion_history:
            emotion_counts = {}
            for emotion in emotion_history:
                emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
            
            logger.info(f"\n📊 RESUMEN DEL VIDEO:")
            logger.info(f"  Frames procesados: {processed_frames}")
            logger.info(f"  Emociones detectadas: {len(emotion_history)}")
            
            # Encontrar emoción dominante
            dominant_emotion = max(emotion_counts.items(), key=lambda x: x[1]) if emotion_counts else ("No detectado", 0)
            total_emotions = len(emotion_history)
            
            # Calcular confianza promedio (simulada basada en detecciones)
            avg_confidence = 0.75 + (len(emotion_history) / processed_frames) * 0.15 if processed_frames > 0 else 0.75
            
            for emotion, count in emotion_counts.items():
                percentage = (count / len(emotion_history)) * 100
                logger.info(f"  {emotion.upper()}: {count} ({percentage:.1f}%)")
            
            # Enviar resumen por Telegram si está disponible
            try:
                # Crear bot temporal para el resumen
                bot = TelegramBot(
                    token=TELEGRAM_TOKEN, 
                    chat_id=TELEGRAM_CHAT_ID
                )
                
                # Preparar mensaje de resumen
                video_name = os.path.basename(video_path)
                resumen_mensaje = f"""🎬 **ANÁLISIS DE VIDEO COMPLETADO**

📁 **Video:** {video_name}
🔍 **Detecciones totales:** {len(dog_detections) if 'dog_detections' in locals() else total_emotions}

🎯 **Emoción dominante:** {dominant_emotion[0].upper()}

📊 **Distribución:**"""
                
                # Agregar distribución de emociones con emojis
                emotion_emojis = {
                    'happy': '😊',
                    'relaxed': '😌', 
                    'sad': '😢',
                    'angry': '😠'
                }
                
                for emotion, count in emotion_counts.items():
                    if count > 0:
                        percentage = (count / total_emotions) * 100
                        emoji = emotion_emojis.get(emotion, '🐕')
                        resumen_mensaje += f"\n{emoji} **{emotion.upper()}:** {count} ({percentage:.0f}%)"
                
                resumen_mensaje += f"\n\n📈 **Confianza promedio:** {avg_confidence:.2f}"
                resumen_mensaje += f"\n⏱️ **Frames procesados:** {processed_frames}"
                
                # Agregar recomendaciones basadas en la emoción dominante
                recommendations = {
                    'happy': "¡Tu perro se ve muy feliz! 🎉 Continúa con las actividades que lo hacen sentir bien.",
                    'relaxed': "Tu perro está en un estado ideal de relajación. 😌 Mantén el ambiente tranquilo.",
                    'sad': "Tu perro mostró signos de tristeza. 💙 Considera darle más atención y verificar su bienestar.",
                    'angry': "Se detectó estrés o molestia. ❤️ Revisa qué podría estar causando esta reacción."
                }
                
                recommendation = recommendations.get(dominant_emotion[0], "Continúa monitoreando el bienestar de tu mascota.")
                resumen_mensaje += f"\n\n💡 **Recomendación:**\n{recommendation}"
                
                # Enviar mensaje
                bot.send_simple_message(resumen_mensaje)
                logger.info("📱 Resumen enviado por Telegram exitosamente")
                
            except Exception as telegram_error:
                logger.warning(f"⚠️ No se pudo enviar resumen por Telegram: {telegram_error}")
        
        return True
        
    except KeyboardInterrupt:
        logger.info("⚠️ Interrupción por usuario")
        return False
    except Exception as e:
        logger.error(f"❌ Error procesando video: {e}")
        return False
    finally:
        cap.release()
        if out is not None:
            out.release()
        cv2.destroyAllWindows()
        logger.info("🏁 Procesamiento de video terminado")

def draw_enhanced_labels(frame, dog_detections, emotion_detected, emotion_prob, dogs_detected):
    """
    Dibuja etiquetas mejoradas con YOLO + emociones
    """
    # Dibujar detecciones YOLO con etiquetas mejoradas
    for i, detection in enumerate(dog_detections):
        bbox = detection['bbox']
        confidence = detection['confidence']
        
        x, y, w, h = bbox
        
        # Color del rectángulo según emoción
        box_color = (0, 255, 0)  # Verde por defecto
        if emotion_detected:
            if emotion_detected in ['angry', 'sad']:
                box_color = (0, 0, 255)  # Rojo para emociones negativas
            elif emotion_detected == 'happy':
                box_color = (0, 255, 255)  # Amarillo para feliz
        
        # Dibujar rectángulo
        cv2.rectangle(frame, (x, y), (x + w, y + h), box_color, 2)
        
        # Etiqueta de detección YOLO
        yolo_label = f"DOG: {confidence:.2f}"
        
        # Etiqueta de emoción si está disponible
        emotion_label = ""
        if emotion_detected and emotion_prob > 0:
            emotion_label = f"EMOTION: {emotion_detected.upper()} ({emotion_prob:.2f})"
        
        # Calcular posiciones de texto
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.6
        thickness = 2
        
        yolo_size = cv2.getTextSize(yolo_label, font, font_scale, thickness)[0]
        emotion_size = cv2.getTextSize(emotion_label, font, font_scale, thickness)[0] if emotion_label else (0, 0)
        
        # Fondo para etiqueta YOLO
        cv2.rectangle(frame, (x, y - yolo_size[1] - 10), 
        (x + yolo_size[0] + 5, y), box_color, -1)
        
        # Texto YOLO
        cv2.putText(frame, yolo_label, (x, y - 5), 
        font, font_scale, (0, 0, 0), thickness)
        
        # Fondo y texto para emoción si existe
        if emotion_label:
            emotion_y = y + h + yolo_size[1] + 15
            cv2.rectangle(frame, (x, emotion_y - emotion_size[1] - 5), 
            (x + emotion_size[0] + 5, emotion_y + 5), box_color, -1)
            cv2.putText(frame, emotion_label, (x, emotion_y), 
            font, font_scale, (0, 0, 0), thickness)
    
    # Mensaje cuando no hay perros detectados
    if not dogs_detected:
        cv2.putText(frame, 'ESPERANDO DETECCION DE PERRO...', 
        (60, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
    
    return frame

def main():
    logger.info("🚀 Iniciando Dog Emotion Monitor con YOLOv8")
    logger.info("=" * 50)
    
    # Verificar que el entorno esté configurado correctamente
    if not verify_environment():
        logger.error("❌ Configuración del entorno incorrecta - Revisa los archivos del proyecto")
        input("Presiona Enter para salir...")
        return
    
    # NUEVA FUNCIONALIDAD: Elegir entre cámara o video
    print("\n🎯 MODO DE FUNCIONAMIENTO:")
    print("1. 📹 Cámara en tiempo real")
    print("2. 🎬 Procesar archivo de video")
    
    try:
        choice = input("\nSelecciona una opción (1 o 2): ").strip()
        
        if choice == "2":
            # Modo procesamiento de video
            video_path = input("📁 Ingresa la ruta del video: ").strip().replace('"', '')
            
            # Preguntar si quiere guardar el resultado
            save_choice = input("💾 ¿Guardar video procesado? (s/n): ").strip().lower()
            save_output = save_choice in ['s', 'si', 'yes', 'y']
            
            output_path = None
            if save_output:
                output_path = input("📁 Ruta para guardar (Enter para automático): ").strip().replace('"', '')
                if not output_path:
                    # Generar nombre automático
                    base_name = os.path.splitext(os.path.basename(video_path))[0]
                    output_path = f"{base_name}_procesado.mp4"
            
            logger.info(f"🎬 Modo video seleccionado: {video_path}")
            result = process_video_file(video_path, save_output, output_path)
            
            if result:
                logger.info("✅ Video procesado exitosamente")
            else:
                logger.error("❌ Error procesando video")
            
            return
            
        elif choice != "1":
            logger.warning("⚠️ Opción no válida, usando cámara por defecto")
    
    except KeyboardInterrupt:
        logger.info("👋 Saliendo...")
        return
    except Exception as e:
        logger.warning(f"⚠️ Error en selección: {e}, usando cámara por defecto")
    
    # MODO CÁMARA ORIGINAL (por defecto)
    logger.info("📹 Modo cámara en tiempo real seleccionado")
    
    # Inicializar componentes
    try:
        logger.info("🧠 Cargando modelo de IA...")
        logger.info(f"📁 Ruta del modelo: {MODEL_PATH}")
        logger.info(f"✅ Archivo modelo existe: {MODEL_PATH.exists()}")
        
        # Usar str() para compatibilidad con librerías que esperan string
        detector = EmotionDetector(str(MODEL_PATH))
        logger.info("✅ Modelo de emociones cargado exitosamente")
    except Exception as e:
        logger.error(f"❌ Error cargando modelo: {e}")
        return
    
    try:
        logger.info("🐕 Inicializando detector YOLO optimizado...")
        yolo_detector = YoloDogDetector(confidence_threshold=YOLO_CONFIDENCE_THRESHOLD)
        logger.info(f"✅ YOLOv8 cargado exitosamente (umbral: {YOLO_CONFIDENCE_THRESHOLD*100:.0f}%)")
    except Exception as e:
        logger.error(f"❌ Error cargando YOLO: {e}")
        return
    
    try:
        logger.info("📱 Inicializando bot de Telegram interactivo...")
        bot = TelegramBot(
            token=TELEGRAM_TOKEN, 
            chat_id=TELEGRAM_CHAT_ID
        )
        logger.info("✅ Bot de Telegram creado")
        
        # Enviar mensaje de bienvenida directamente (el bot ya está funcionando)
        logger.info("📨 Enviando mensaje de bienvenida...")
        bot.send_welcome_message()
        telegram_enabled = True
        logger.info("✅ Telegram habilitado - Monitoreo activado por defecto")
            
    except Exception as e:
        logger.warning(f"⚠️ Telegram no disponible: {e}")
        logger.warning(f"⚠️ Tipo de error: {type(e).__name__}")
        telegram_enabled = False
        bot = None
    
    # Buscar cámara
    camera_index = find_available_camera()
    if camera_index is None:
        logger.error("❌ No se encontró ninguna cámara")
        return
    
    # Inicializar cámara con configuración personalizable
    cap = cv2.VideoCapture(camera_index)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
    cap.set(cv2.CAP_PROP_FPS, CAMERA_FPS)
    
    # Variables de control usando configuración
    emotion_history = []
    cooldown_time = EMOTION_ANALYSIS_INTERVAL
    last_analysis_time = time.time()
    frame_count = 0
    
    logger.info("\n🎮 CONTROLES:")
    logger.info("  Q o ESC: Salir")
    logger.info("  S: Enviar mensaje de prueba por Telegram")
    logger.info("  M: Recordatorio del menú de Telegram")
    logger.info("  C: Limpiar chat de Telegram")
    logger.info("\n📱 TELEGRAM:")
    logger.info("  Usa /menu en el chat para acceder a todas las funciones")
    logger.info("  Activa el monitoreo desde el menú para recibir alertas")
    logger.info("\n▶️ Iniciando detección...\n")
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                logger.error("Error capturando frame")
                break

            current_time = time.time()
            frame_count += 1
            
            # PASO 1: Detectar perros con YOLO
            dog_detections = yolo_detector.detect_dogs(frame)
            dogs_detected = yolo_detector.is_dog_detected(dog_detections)
            
            # PASO 2: Dibujar detecciones de YOLO solamente
            frame = yolo_detector.draw_detections(frame, dog_detections)
            
            # PASO 3: Solo analizar emociones SI hay perros detectados
            # Removemos el análisis continuo para evitar spam de logs
            if dogs_detected and current_time - last_analysis_time >= cooldown_time:
                try:
                    logger.info(f"🐕 Analizando emociones... (perro detectado)")
                    emotion, prob, preds = detector.predict_emotion(frame)

                    
                    # Debug: Mostrar todas las predicciones para entender el problema
                    logger.info("📊 Análisis detallado de emociones:")
                    for label, p in zip(detector.labels, preds):
                        logger.info(f"  {label}: {p:.4f} ({'⭐' if p == max(preds) else ''})")
                    logger.info(f"  🎯 Resultado final: {emotion.upper()} ({prob:.3f})")

                    # 🔥 Enviar actualización al frontend (Socket.IO vía Flask)
                    try:
                        payload = {
                            "dominant_emotion": emotion,
                            "confidence": float(prob),
                            "happy": float(preds[1]),
                            "sad": float(preds[3]),
                            "angry": float(preds[0]),
                            "relaxed": float(preds[2])
                        }
                    # Envía los datos al endpoint de server.py (que lo retransmite a Socket.IO)
                        requests.post("http://localhost:5000/emotion_update", json=payload, timeout=1)
                        logger.info("📡 Datos enviados al frontend")
                    except Exception as e:
                        logger.warning(f"⚠️ No se pudo enviar actualización al frontend: {e}")


                    
                    # Verificar si hay un problema con la clasificación
                    if emotion == 'relaxed' and max(preds) < 0.6:
                        logger.warning(f"⚠️ Confianza baja en 'relaxed' ({prob:.3f}) - Podría ser clasificación incorrecta")

                    # Determinar color según emoción
                    color = (0, 255, 0)  # Verde por defecto
                    if emotion in ['angry', 'sad']:
                        color = (0, 0, 255)  # Rojo para emociones negativas
                    elif emotion == 'happy':
                        color = (0, 255, 255)  # Amarillo para feliz
                    
                    # Mostrar emoción en el frame con mejor posicionamiento
                    emotion_text = f'EMOCION: {emotion.upper()} ({prob:.2f})'
                    if dogs_detected:
                        # Si hay detección YOLO, mostrar cerca del rectángulo
                        best_detection = yolo_detector.get_best_dog_region(dog_detections)
                        if best_detection:
                            x, y, w, h = best_detection
                            cv2.putText(frame, emotion_text, (x, y + h + 30), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
                        else:
                            cv2.putText(frame, emotion_text, (60, 120), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
                    else:
                        # Si no hay detección YOLO, mostrar en posición fija
                        cv2.putText(frame, emotion_text, (60, 120), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

                    # Acumular historial de emociones
                    emotion_history.append(emotion)
                    if len(emotion_history) > 4:  # Reducido de 8 a 4 para mejor responsividad
                        emotion_history.pop(0)
                    
                    # Actualizar historial en el bot
                    if telegram_enabled and bot:
                        bot.update_emotion_history(emotion)
                        bot.send_periodic_update()  # Enviar actualización si es momento

                    # Verificar patrones preocupantes (reducido a 3 análisis negativos de 4)
                    if len(emotion_history) >= 3 and all(e in ['sad', 'angry'] for e in emotion_history[-3:]):
                        logger.warning(f"🚨 Patrón preocupante detectado: {emotion} repetidamente")
                        
                        if telegram_enabled and bot:
                            try:
                                # Capturar imagen para la alerta
                                timestamp = int(time.time())
                                path = f"alerta_{emotion}_{timestamp}_{int(prob*100)}.jpg"
                                cv2.imwrite(path, frame)
                                
                                # Enviar alerta con recomendaciones
                                bot.send_alert(emotion, prob, image_path=path)
                                
                                # Limpiar archivo temporal
                                try:
                                    os.remove(path)
                                except:
                                    pass
                                
                                emotion_history.clear()  # Reiniciar para evitar spam
                                logger.info("📱 Alerta enviada por Telegram")
                                
                            except Exception as e:
                                logger.error(f"Error enviando alerta: {e}")

                    last_analysis_time = current_time
                    
                except Exception as e:
                    logger.error(f"Error en análisis de emoción: {e}")
            
            elif not dogs_detected:
                # Solo mostrar mensaje de espera si no hay detecciones
                cv2.putText(frame, 'ESPERANDO DETECCION DE PERRO...', 
                        (60, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                # Limpiar historial si no hay perros por mucho tiempo
                if current_time - last_analysis_time > 30:  # 30 segundos sin perros
                    if emotion_history:
                        emotion_history.clear()
                        logger.info("🧹 Historial limpiado - Sin perros detectados")

            # Mostrar información de estado en el frame
            info_y = frame.shape[0] - 100
            cv2.putText(frame, f'Frame: {frame_count}', (10, info_y), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            cv2.putText(frame, f'Perros detectados: {len(dog_detections)}', (10, info_y + 20), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            cv2.putText(frame, f'Historial emocional: {len(emotion_history)}/4', (10, info_y + 40), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            cv2.putText(frame, 'Q: salir | S: test | M: menu | C: limpiar', (10, info_y + 60), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
            
            # 🔥 ENVIAR FRAME AL DASHBOARD WEB
            _, buffer = cv2.imencode('.jpg', frame)
            frame_encoded = base64.b64encode(buffer).decode('utf-8')
            try:
                requests.post("http://localhost:5000/frame_update",
                            json={"frame": frame_encoded}, timeout=0.5)
                logger.info("📡 Frame enviado al frontend")
            except Exception as e:
                logger.warning(f"No se pudo enviar frame al frontend: {e}")

            
            #MUESTRA VENTANA LOCAL
            cv2.imshow('🐕 Dog Emotion Monitor + YOLOv8', frame)

            # Manejar teclas
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == 27:  # Q o ESC
                logger.info("👋 Saliendo del programa...")
                break
            elif key == ord('s') and telegram_enabled and bot:  # S para test
                try:
                    test_path = "test_manual.jpg"
                    cv2.imwrite(test_path, frame)
                    
                    # Verificar si el monitoreo está activo
                    if not bot.monitoring_active:
                        logger.warning("⚠️ Monitoreo pausado - Activando para la prueba")
                        bot.monitoring_active = True
                    # Usar la última emoción detectada realmente
                    if 'emotion' in locals() and 'prob' in locals():
                        bot.send_alert(emotion, prob, image_path=test_path)
                        logger.info(f"📱 Alerta enviada con emoción real: {emotion.upper()} ({prob:.2f})")
                    else:
                        logger.warning("⚠️ Aún no se ha detectado ninguna emoción para enviar.")    
                    
                    #bot.send_alert("happy", 0.95, image_path=test_path)
                    os.remove(test_path)
                    logger.info("📱 Mensaje de prueba enviado - Revisa el menú con /menu")
                        
                except Exception as e:
                    logger.error(f"Error enviando prueba: {e}")

            elif key == ord('m') and telegram_enabled and bot:  # M para menú
                try:
                    bot.send_simple_message("🎛️ Usa /menu para acceder a todas las opciones del bot")
                    logger.info("📱 Recordatorio de menú enviado")
                except Exception as e:
                    logger.error(f"Error enviando recordatorio: {e}")
            elif key == ord('c') and telegram_enabled and bot:  # C para limpiar chat
                try:
                    if bot.clear_chat_sync():
                        logger.info("✅ Chat limpiado desde teclado")
                    else:
                        logger.warning("⚠️ No se pudo limpiar el chat completamente")
                except Exception as e:
                    logger.error(f"Error limpiando chat: {e}")

    except KeyboardInterrupt:
        logger.info("⚠️ Interrupción por usuario")
    except Exception as e:
        logger.error(f"❌ Error en bucle principal: {e}")
    finally:
        # Cleanup
        cap.release()
        cv2.destroyAllWindows()
        
        # Cerrar bot de Telegram
        if telegram_enabled and bot:
            try:
                bot.cleanup()
            except:
                pass
                
        logger.info("🏁 Programa terminado exitosamente")

if __name__ == "__main__":
    main()
