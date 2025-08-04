from flask import Flask, render_template, request, jsonify, send_file
from flask_socketio import SocketIO, emit
import cv2
import base64
import numpy as np
import os
import time
import json
import logging
import threading
from datetime import datetime
from collections import deque
from concurrent.futures import ThreadPoolExecutor

# Importar utilidades
from utils.cam_utils import EmotionDetector
from utils.telegram_simple import SimpleTelegramBot as TelegramBot
from utils.yolo_dog_detector import YoloDogDetector

# Configurar logging con formato mejorado
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(name)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Configuración de Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = 'dog_emotion_secret_key_2024'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Variables globales con thread safety
detector = None
yolo_detector = None
telegram_bot = None
analysis_count = {}  # Contador por IP
camera_active = False
video_capture = None
emotion_history = deque(maxlen=100)  # Historial circular de emociones
alert_cooldown = {}  # Control de frecuencia de alertas
executor = ThreadPoolExecutor(max_workers=4)  # Pool para tareas asíncronas

# Configuración
ANALYSIS_LIMIT = 5  # Límite de análisis gratuitos por IP
TELEGRAM_TOKEN = "7565394500:AAEqYMlT4mQFGTlL8slsSrlrst3MZmeMzIg"
TELEGRAM_CHAT_ID = "1846987938"
ALERT_COOLDOWN_SECONDS = 30  # Tiempo mínimo entre alertas
EMOTION_THRESHOLD = 0.7  # Umbral de confianza para alertas

# Configuración de rendimiento
PERFORMANCE_CONFIG = {
    'frame_skip': 5,  # Procesar 1 de cada 5 frames en video
    'max_video_seconds': 120,  # Máximo 2 minutos de video
    'realtime_fps': 10,  # FPS para análisis en tiempo real
    'batch_size': 1,  # Tamaño de lote para predicciones
    'cache_enabled': True
}

def initialize_models():
    """Inicializa los modelos de IA con optimizaciones"""
    global detector, yolo_detector, telegram_bot
    try:
        logger.info("🧠 Cargando modelo de emociones...")
        detector = EmotionDetector("modelo/mejor_modelo_83.h5")
        logger.info("✅ Modelo de emociones cargado")
        
        logger.info("🐕 Inicializando detector YOLO...")
        yolo_detector = YoloDogDetector(confidence_threshold=0.60)
        logger.info("✅ YOLO detector cargado")
        
        logger.info("📱 Inicializando bot de Telegram...")
        telegram_bot = TelegramBot(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID)
        
        # Verificar conexión con Telegram
        if telegram_bot.test_connection():
            logger.info("✅ Bot de Telegram conectado exitosamente")
            # Enviar mensaje de inicio
            telegram_bot.send_welcome_message()
        else:
            logger.error("❌ No se pudo conectar con Telegram")
        
        return True
    except Exception as e:
        logger.error(f"❌ Error inicializando modelos: {e}")
        return False

def get_client_ip():
    """Obtiene la IP del cliente de forma robusta"""
    try:
        if request.environ.get('HTTP_X_FORWARDED_FOR'):
            return request.environ['HTTP_X_FORWARDED_FOR'].split(',')[0]
        elif request.environ.get('HTTP_X_REAL_IP'):
            return request.environ['HTTP_X_REAL_IP']
        else:
            return request.environ.get('REMOTE_ADDR', '127.0.0.1')
    except:
        return '127.0.0.1'

def check_analysis_limit(ip):
    """Verifica si el cliente ha alcanzado el límite de análisis"""
    if ip not in analysis_count:
        analysis_count[ip] = 0
    return analysis_count[ip] < ANALYSIS_LIMIT

def increment_analysis_count(ip):
    """Incrementa el contador de análisis para una IP"""
    if ip not in analysis_count:
        analysis_count[ip] = 0
    analysis_count[ip] += 1

def get_remaining_analyses(ip):
    """Obtiene el número de análisis restantes"""
    if ip not in analysis_count:
        analysis_count[ip] = 0
    return max(0, ANALYSIS_LIMIT - analysis_count[ip])

def should_send_alert(emotion, probability):
    """Determina si se debe enviar una alerta basado en cooldown y umbral"""
    current_time = time.time()
    
    # Verificar umbral de probabilidad
    if probability < EMOTION_THRESHOLD:
        return False
    
    # Solo alertar sobre emociones negativas
    if emotion not in ['angry', 'sad']:
        return False
    
    # Verificar cooldown
    alert_key = f"{emotion}_{probability:.1f}"
    if alert_key in alert_cooldown:
        if current_time - alert_cooldown[alert_key] < ALERT_COOLDOWN_SECONDS:
            return False
    
    # Actualizar cooldown
    alert_cooldown[alert_key] = current_time
    return True

def send_telegram_alert_async(emotion, probability, image_path=None):
    """Envía alerta a Telegram de forma asíncrona"""
    def _send():
        try:
            if telegram_bot and telegram_bot.monitoring_active:
                logger.info(f"📱 Enviando alerta a Telegram: {emotion} ({probability:.2f})")
                success = telegram_bot.send_alert(emotion, probability, image_path)
                if success:
                    logger.info("✅ Alerta enviada exitosamente")
                else:
                    logger.error("❌ Error enviando alerta")
        except Exception as e:
            logger.error(f"❌ Error en envío asíncrono: {e}")
    
    # Ejecutar en thread pool
    executor.submit(_send)

@app.route('/')
def index():
    """Página principal"""
    client_ip = get_client_ip()
    remaining = get_remaining_analyses(client_ip)
    return render_template('index.html', remaining_analyses=remaining)

@app.route('/health')
def health():
    """Endpoint de salud del servidor con más detalles"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'components': {
            'emotion_model': detector is not None,
            'yolo_detector': yolo_detector is not None,
            'telegram_bot': telegram_bot is not None,
            'telegram_connected': telegram_bot.test_connection() if telegram_bot else False
        },
        'performance': {
            'emotion_history_size': len(emotion_history),
            'active_alerts': len(alert_cooldown),
            'camera_active': camera_active
        }
    })

@app.route('/api/analyze', methods=['POST'])
def analyze_emotion():
    """Analiza una imagen/video para detectar emociones Y ENVÍA A TELEGRAM"""
    client_ip = get_client_ip()
    
    # Verificar límite de análisis
    if not check_analysis_limit(client_ip):
        return jsonify({
            'success': False,
            'error': 'limit_reached',
            'message': 'Has alcanzado el límite de análisis gratuitos. ¡Adquiere el plan premium!',
            'remaining': 0
        })
    
    try:
        file = request.files.get('file')
        if not file:
            return jsonify({'success': False, 'error': 'No file provided'})
        
        # Procesar archivo
        file_bytes = np.frombuffer(file.read(), np.uint8)
        
        # Determinar si es imagen o video
        if file.filename.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp')):
            # Procesar imagen
            image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
            result = process_image(image, client_ip, file.filename)
        elif file.filename.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
            # Procesar video
            result = process_video(file_bytes, client_ip, file.filename)
        else:
            return jsonify({'success': False, 'error': 'Formato de archivo no soportado'})
        
        # Incrementar contador solo si el análisis fue exitoso
        if result.get('success'):
            increment_analysis_count(client_ip)
            result['remaining'] = get_remaining_analyses(client_ip)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error en análisis: {e}")
        return jsonify({'success': False, 'error': str(e)})

def process_image(image, client_ip, filename="imagen"):
    """Procesa una imagen individual Y ENVÍA ALERTA A TELEGRAM"""
    try:
        # Detectar perros con YOLO
        dog_detections = yolo_detector.detect_dogs(image)
        dogs_detected = yolo_detector.is_dog_detected(dog_detections)
        
        if not dogs_detected:
            return {
                'success': False,
                'error': 'no_dog_detected',
                'message': 'No se detectaron perros en la imagen'
            }
        
        # Analizar emociones
        emotion, probability, predictions = detector.predict_emotion(image)
        
        # Actualizar historial
        emotion_history.append({
            'emotion': emotion,
            'probability': probability,
            'timestamp': time.time(),
            'source': 'image'
        })
        
        # Actualizar historial en Telegram
        if telegram_bot:
            telegram_bot.update_emotion_history(emotion)
        
        # Crear imagen con detecciones
        result_image = yolo_detector.draw_detections(image, dog_detections)
        
        # Agregar información de emociones
        best_detection = yolo_detector.get_best_dog_region(dog_detections)
        if best_detection:
            x, y, w, h = best_detection
            color = get_emotion_color(emotion)
            cv2.putText(result_image, f'{emotion.upper()}: {probability:.2f}', 
                       (x, y + h + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
        
        # Guardar imagen temporalmente para Telegram
        temp_image_path = None
        if should_send_alert(emotion, probability):
            temp_image_path = f"temp_alert_{int(time.time())}.jpg"
            cv2.imwrite(temp_image_path, result_image)
            
            # ENVIAR ALERTA A TELEGRAM
            logger.info(f"🚨 Enviando alerta a Telegram: {emotion} - {probability:.2f}")
            send_telegram_alert_async(emotion, probability, temp_image_path)
        
        # Convertir imagen a base64
        _, buffer = cv2.imencode('.jpg', result_image)
        image_base64 = base64.b64encode(buffer).decode('utf-8')
        
        # Limpiar imagen temporal después de un delay
        if temp_image_path:
            def cleanup():
                time.sleep(5)  # Esperar 5 segundos
                try:
                    if os.path.exists(temp_image_path):
                        os.remove(temp_image_path)
                except:
                    pass
            threading.Thread(target=cleanup, daemon=True).start()
        
        return {
            'success': True,
            'type': 'image',
            'filename': filename,
            'emotion': emotion,
            'probability': float(probability),
            'predictions': {
                'happy': float(predictions[1]),
                'sad': float(predictions[3]),
                'angry': float(predictions[0]),
                'relaxed': float(predictions[2])
            },
            'image': image_base64,
            'dogs_detected': len(dog_detections),
            'telegram_alert_sent': temp_image_path is not None
        }
        
    except Exception as e:
        logger.error(f"Error procesando imagen: {e}")
        return {'success': False, 'error': str(e)}

def process_video(file_bytes, client_ip, filename="video"):
    """Procesa un video completo Y ENVÍA RESUMEN A TELEGRAM"""
    try:
        # Guardar video temporalmente
        temp_path = f"temp_video_{int(time.time())}.mp4"
        with open(temp_path, 'wb') as f:
            f.write(file_bytes)
        
        cap = cv2.VideoCapture(temp_path)
        
        # Obtener información del video
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps if fps > 0 else 0
        
        # Verificar duración máxima
        if duration > PERFORMANCE_CONFIG['max_video_seconds']:
            cap.release()
            os.remove(temp_path)
            return {
                'success': False,
                'error': 'video_too_long',
                'message': f'Video demasiado largo. Máximo {PERFORMANCE_CONFIG["max_video_seconds"]} segundos.'
            }
        
        emotions_history = []
        frames_processed = 0
        frames_with_dogs = 0
        frame_skip = PERFORMANCE_CONFIG['frame_skip']
        
        logger.info(f"📹 Procesando video: {filename} ({duration:.1f}s, {total_frames} frames)")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            frames_processed += 1
            
            # Procesar solo cada N frames
            if frames_processed % frame_skip == 0:
                dog_detections = yolo_detector.detect_dogs(frame)
                dogs_detected = yolo_detector.is_dog_detected(dog_detections)
                
                if dogs_detected:
                    frames_with_dogs += 1
                    emotion, probability, predictions = detector.predict_emotion(frame)
                    
                    emotions_history.append({
                        'emotion': emotion,
                        'probability': float(probability),
                        'frame': frames_processed,
                        'timestamp': frames_processed / fps
                    })
                    
                    # Actualizar historial global
                    emotion_history.append({
                        'emotion': emotion,
                        'probability': probability,
                        'timestamp': time.time(),
                        'source': 'video'
                    })
        
        cap.release()
        os.remove(temp_path)  # Limpiar archivo temporal
        
        if not emotions_history:
            return {
                'success': False,
                'error': 'no_dogs_in_video',
                'message': 'No se detectaron perros en el video'
            }
        
        # Calcular estadísticas
        emotion_counts = {}
        total_probability = 0
        high_confidence_alerts = []
        
        for entry in emotions_history:
            emotion = entry['emotion']
            probability = entry['probability']
            
            if emotion not in emotion_counts:
                emotion_counts[emotion] = 0
            emotion_counts[emotion] += 1
            total_probability += probability
            
            # Registrar alertas de alta confianza
            if emotion in ['angry', 'sad'] and probability > EMOTION_THRESHOLD:
                high_confidence_alerts.append(entry)
        
        dominant_emotion = max(emotion_counts.items(), key=lambda x: x[1])
        avg_confidence = total_probability / len(emotions_history)
        
        # ENVIAR RESUMEN A TELEGRAM
        if telegram_bot and emotion_counts:
            logger.info("📱 Enviando resumen de video a Telegram...")
            
            # Preparar estadísticas para Telegram
            video_stats = {
                'video_name': filename,
                'total_emotions': len(emotions_history),
                'emotion_distribution': emotion_counts,
                'dominant_emotion': dominant_emotion[0],
                'confidence_avg': avg_confidence,
                'frames_processed': frames_processed,
                'dog_detection_rate': (frames_with_dogs / (frames_processed / frame_skip)) * 100,
                'processing_speed': frames_processed / duration if duration > 0 else 0,
                'output_file': None  # No guardamos archivo en este caso
            }
            
            # Enviar resumen
            telegram_bot.send_video_summary(video_stats)
            
            # Actualizar historial en Telegram
            for emotion in emotion_counts:
                for _ in range(emotion_counts[emotion]):
                    telegram_bot.update_emotion_history(emotion)
            
            # Si hay alertas de alta confianza, enviar la más relevante
            if high_confidence_alerts and dominant_emotion[0] in ['angry', 'sad']:
                best_alert = max(high_confidence_alerts, key=lambda x: x['probability'])
                send_telegram_alert_async(
                    best_alert['emotion'], 
                    best_alert['probability']
                )
        
        return {
            'success': True,
            'type': 'video',
            'filename': filename,
            'duration': float(duration),
            'total_frames': total_frames,
            'frames_analyzed': len(emotions_history),
            'frames_with_dogs': frames_with_dogs,
            'dominant_emotion': dominant_emotion[0],
            'dominant_emotion_count': dominant_emotion[1],
            'emotion_distribution': emotion_counts,
            'average_confidence': float(avg_confidence),
            'timeline': emotions_history[:50],  # Primeros 50 resultados
            'high_confidence_alerts': len(high_confidence_alerts),
            'telegram_summary_sent': telegram_bot is not None
        }
        
    except Exception as e:
        logger.error(f"Error procesando video: {e}")
        return {'success': False, 'error': str(e)}

def get_emotion_color(emotion):
    """Obtiene el color BGR para una emoción"""
    colors = {
        'happy': (0, 255, 255),    # Amarillo
        'relaxed': (0, 255, 0),    # Verde
        'sad': (255, 0, 0),        # Azul
        'angry': (0, 0, 255)       # Rojo
    }
    return colors.get(emotion, (255, 255, 255))

@app.route('/api/payment', methods=['POST'])
def process_payment():
    """Simula el procesamiento de pago"""
    try:
        data = request.get_json()
        
        # Validar datos de pago (simulado)
        required_fields = ['cardNumber', 'expiryDate', 'cvv', 'cardName']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'error': f'Campo requerido: {field}'
                })
        
        # Simular procesamiento
        time.sleep(2)
        
        # Resetear contador para la IP
        client_ip = get_client_ip()
        analysis_count[client_ip] = -999999  # Usuario premium sin límite
        
        # Generar código de acceso
        access_code = f"PREMIUM_{int(time.time())}"
        
        # Notificar a Telegram sobre nuevo usuario premium
        if telegram_bot:
            telegram_bot.send_simple_message(
                f"🎉 **NUEVO USUARIO PREMIUM**\n\n"
                f"IP: {client_ip}\n"
                f"Código: {access_code}\n"
                f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
        
        return jsonify({
            'success': True,
            'message': 'Pago procesado exitosamente',
            'access_code': access_code,
            'telegram_access': True
        })
        
    except Exception as e:
        logger.error(f"Error procesando pago: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/telegram-access', methods=['POST'])
def get_telegram_access():
    """Proporciona acceso a Telegram después del pago"""
    try:
        # URL real del bot (usar el username real si existe)
        telegram_url = "https://t.me/DogEmotionAI_bot"
        
        return jsonify({
            'success': True,
            'telegram_url': telegram_url,
            'bot_username': '@DogEmotionAI_bot',
            'chat_id': TELEGRAM_CHAT_ID,
            'instructions': [
                '1. Abre Telegram y busca @DogEmotionAI_bot',
                '2. Inicia conversación con /start',
                '3. Usa /menu para ver todas las opciones',
                '4. ¡Disfruta del monitoreo 24/7 de tu mascota!'
            ]
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo acceso Telegram: {e}")
        return jsonify({'success': False, 'error': str(e)})

# Eventos de WebSocket para cámara en tiempo real
@socketio.on('start_detection')
def handle_start_detection():
    """Inicia detección en tiempo real CON ALERTAS A TELEGRAM"""
    global camera_active, video_capture
    
    client_ip = get_client_ip()
    if not check_analysis_limit(client_ip):
        emit('detection_error', {
            'error': 'limit_reached',
            'message': 'Límite de análisis alcanzado'
        })
        return
    
    try:
        camera_active = True
        video_capture = cv2.VideoCapture(0)
        
        if not video_capture.isOpened():
            # Intentar con otras cámaras
            for i in range(1, 5):
                video_capture = cv2.VideoCapture(i)
                if video_capture.isOpened():
                    break
            
            if not video_capture.isOpened():
                emit('detection_error', {'error': 'No se pudo acceder a la cámara'})
                return
        
        # Configurar cámara para mejor rendimiento
        video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        video_capture.set(cv2.CAP_PROP_FPS, 30)
        
        emit('detection_started', {'status': 'success'})
        
        # Notificar a Telegram
        if telegram_bot:
            telegram_bot.send_simple_message(
                "📹 **Análisis en tiempo real iniciado**\n\n"
                "Sistema de monitoreo activado desde la aplicación web."
            )
        
        # Iniciar bucle de captura
        socketio.start_background_task(target=camera_loop_with_telegram)
        
    except Exception as e:
        logger.error(f"Error iniciando detección: {e}")
        emit('detection_error', {'error': str(e)})

@socketio.on('stop_detection')
def handle_stop_detection():
    """Detiene la detección en tiempo real"""
    global camera_active, video_capture
    
    camera_active = False
    if video_capture:
        video_capture.release()
        video_capture = None
    
    # Notificar a Telegram
    if telegram_bot:
        telegram_bot.send_simple_message(
            "⏹️ **Análisis en tiempo real detenido**\n\n"
            "El monitoreo desde la cámara web ha finalizado."
        )
    
    emit('detection_stopped', {'status': 'success'})

def camera_loop_with_telegram():
    """Bucle principal de captura de cámara CON INTEGRACIÓN TELEGRAM"""
    global camera_active, video_capture
    
    frame_count = 0
    last_alert_time = 0
    emotion_buffer = deque(maxlen=30)  # Buffer de 30 detecciones
    
    while camera_active and video_capture:
        try:
            ret, frame = video_capture.read()
            if not ret:
                logger.error("Error capturando frame")
                break
            
            frame_count += 1
            current_time = time.time()
            
            # Procesar frame
            if detector and yolo_detector:
                # Detectar perros
                dog_detections = yolo_detector.detect_dogs(frame)
                dogs_detected = yolo_detector.is_dog_detected(dog_detections)
                
                frame_processed = yolo_detector.draw_detections(frame, dog_detections)
                
                # Analizar emociones si hay perros
                emotion_data = None
                if dogs_detected:
                    emotion, probability, predictions = detector.predict_emotion(frame)
                    
                    emotion_data = {
                        'emotion': emotion,
                        'probability': float(probability),
                        'happy': float(predictions[1]),
                        'sad': float(predictions[3]),
                        'angry': float(predictions[0]),
                        'relaxed': float(predictions[2]),
                        'dominant_emotion': emotion,
                        'confidence': float(probability),
                        'timestamp': current_time
                    }
                    
                    # Agregar al buffer
                    emotion_buffer.append(emotion_data)
                    
                    # Actualizar historial global
                    emotion_history.append({
                        'emotion': emotion,
                        'probability': probability,
                        'timestamp': current_time,
                        'source': 'realtime'
                    })
                    
                    # Actualizar historial en Telegram
                    if telegram_bot:
                        telegram_bot.update_emotion_history(emotion)
                    
                    # ENVIAR ALERTA A TELEGRAM si es necesario
                    if should_send_alert(emotion, probability) and current_time - last_alert_time > ALERT_COOLDOWN_SECONDS:
                        # Guardar frame para la alerta
                        alert_image_path = f"realtime_alert_{int(current_time)}.jpg"
                        cv2.imwrite(alert_image_path, frame_processed)
                        
                        logger.info(f"🚨 Alerta en tiempo real: {emotion} ({probability:.2f})")
                        send_telegram_alert_async(emotion, probability, alert_image_path)
                        last_alert_time = current_time
                        
                        # Limpiar imagen después
                        def cleanup():
                            time.sleep(5)
                            try:
                                if os.path.exists(alert_image_path):
                                    os.remove(alert_image_path)
                            except:
                                pass
                        threading.Thread(target=cleanup, daemon=True).start()
                    
                    # Agregar texto de emoción al frame
                    best_detection = yolo_detector.get_best_dog_region(dog_detections)
                    if best_detection:
                        x, y, w, h = best_detection
                        color = get_emotion_color(emotion)
                        cv2.putText(frame_processed, f'{emotion.upper()}: {probability:.2f}', 
                                   (x, y + h + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
                
                # Enviar actualización periódica a Telegram (cada 60 segundos)
                if frame_count % (60 * PERFORMANCE_CONFIG['realtime_fps']) == 0 and telegram_bot:
                    telegram_bot.send_periodic_update()
                    
            else:
                frame_processed = frame
            
            # Agregar estadísticas al frame
            cv2.putText(frame_processed, f'Frame: {frame_count}', (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            # Convertir frame a base64
            _, buffer = cv2.imencode('.jpg', frame_processed, [cv2.IMWRITE_JPEG_QUALITY, 80])
            frame_base64 = base64.b64encode(buffer).decode('utf-8')
            
            # Emitir frame
            socketio.emit('frame_update', {'frame': frame_base64})
            
            # Emitir datos de emoción si están disponibles
            if emotion_data:
                socketio.emit('emotion_update', emotion_data)
            
            # Control de FPS
            time.sleep(1.0 / PERFORMANCE_CONFIG['realtime_fps'])
            
        except Exception as e:
            logger.error(f"Error en bucle de cámara: {e}")
            break
    
    camera_active = False
    logger.info("📹 Bucle de cámara terminado")

@socketio.on('test_telegram')
def handle_test_telegram():
    """Envía mensaje de prueba a Telegram"""
    try:
        if telegram_bot:
            success = telegram_bot.test_connection()
            if success:
                telegram_bot.send_simple_message(
                    "🧪 **MENSAJE DE PRUEBA**\n\n"
                    "✅ Conexión exitosa desde la aplicación web\n"
                    f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )
                emit('telegram_test', {
                    'status': 'success',
                    'message': 'Mensaje enviado a Telegram'
                })
            else:
                emit('telegram_test', {
                    'status': 'error',
                    'message': 'No se pudo conectar con Telegram'
                })
        else:
            emit('telegram_test', {
                'status': 'error',
                'message': 'Bot no disponible'
            })
    except Exception as e:
        logger.error(f"Error enviando test Telegram: {e}")
        emit('telegram_test', {
            'status': 'error',
            'message': str(e)
        })

@socketio.on('get_stats')
def handle_get_stats():
    """Obtiene estadísticas del sistema"""
    try:
        # Calcular estadísticas de emociones
        emotion_stats = {}
        if emotion_history:
            for entry in emotion_history:
                emotion = entry['emotion']
                if emotion not in emotion_stats:
                    emotion_stats[emotion] = 0
                emotion_stats[emotion] += 1
        
        emit('stats_update', {
            'total_analyses': len(emotion_history),
            'emotion_distribution': emotion_stats,
            'active_alerts': len(alert_cooldown),
            'camera_active': camera_active,
            'telegram_connected': telegram_bot is not None
        })
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {e}")

@app.route('/api/clear-history', methods=['POST'])
def clear_history():
    """Limpia el historial de análisis"""
    try:
        client_ip = get_client_ip()
        
        # Limpiar historial
        emotion_history.clear()
        alert_cooldown.clear()
        
        # Limpiar chat de Telegram si está disponible
        if telegram_bot:
            telegram_bot.clear_chat_sync()
        
        logger.info(f"📝 Historial limpiado por {client_ip}")
        
        return jsonify({
            'success': True,
            'message': 'Historial limpiado exitosamente'
        })
    except Exception as e:
        logger.error(f"Error limpiando historial: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.errorhandler(404)
def not_found(error):
    """Manejo de errores 404"""
    return jsonify({'error': 'Endpoint no encontrado'}), 404

@app.errorhandler(500)
def internal_error(error):
    """Manejo de errores 500"""
    logger.error(f"Error interno: {error}")
    return jsonify({'error': 'Error interno del servidor'}), 500

def cleanup_resources():
    """Limpia recursos al cerrar la aplicación"""
    global camera_active, video_capture
    
    logger.info("🧹 Limpiando recursos...")
    
    # Detener cámara
    camera_active = False
    if video_capture:
        video_capture.release()
    
    # Cerrar bot de Telegram
    if telegram_bot:
        telegram_bot.cleanup()
    
    # Cerrar executor
    executor.shutdown(wait=False)
    
    logger.info("✅ Recursos limpiados")

if __name__ == '__main__':
    try:
        # Crear directorios necesarios
        for directory in ['templates', 'static', 'uploads', 'logs']:
            if not os.path.exists(directory):
                os.makedirs(directory)
        
        # Inicializar modelos
        logger.info("🚀 Iniciando Dog Emotion AI - Servidor Web")
        models_loaded = initialize_models()
        
        if not models_loaded:
            logger.warning("⚠️ Modelos no cargados completamente, funcionando en modo limitado")
        
        logger.info("🌐 Servidor disponible en http://localhost:5000")
        logger.info("📱 Bot de Telegram: @DogEmotionAI_bot")
        logger.info("✨ Sistema listo para analizar emociones caninas")
        
        # Ejecutar servidor
        socketio.run(
            app, 
            host='0.0.0.0', 
            port=5000, 
            debug=False,
            use_reloader=False
        )
        
    except KeyboardInterrupt:
        logger.info("\n👋 Cerrando aplicación...")
    except Exception as e:
        logger.error(f"❌ Error fatal: {e}")
    finally:
        cleanup_resources()