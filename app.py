from flask import Flask, render_template, request, jsonify, send_file
from flask_socketio import SocketIO, emit
import cv2
import base64
import numpy as np
import os
import time
import json
from utils.cam_utils import EmotionDetector
from utils.telegram_utils import TelegramBot
from utils.yolo_dog_detector import YoloDogDetector
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dog_emotion_secret_key_2024'
socketio = SocketIO(app, cors_allowed_origins="*")

# Variables globales
detector = None
yolo_detector = None
telegram_bot = None
analysis_count = {}  # Contador por IP
camera_active = False
video_capture = None

# Configuración
ANALYSIS_LIMIT = 5  # Límite de análisis gratuitos por IP
TELEGRAM_TOKEN = "7668982184:AAEXrM7xx0bDKidNOhyi6xjSNYUNRpvu61U"
TELEGRAM_CHAT_ID = "1673887715"

def initialize_models():
    """Inicializa los modelos de IA"""
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
        logger.info("✅ Bot de Telegram inicializado")
        
        return True
    except Exception as e:
        logger.error(f"❌ Error inicializando modelos: {e}")
        # Crear modelos mock para desarrollo
        return False

def get_client_ip():
    """Obtiene la IP del cliente"""
    if request.environ.get('HTTP_X_FORWARDED_FOR') is None:
        return request.environ['REMOTE_ADDR']
    else:
        return request.environ['HTTP_X_FORWARDED_FOR']

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

@app.route('/')
def index():
    """Página principal"""
    client_ip = get_client_ip()
    remaining = get_remaining_analyses(client_ip)
    return render_template('index.html', remaining_analyses=remaining)

@app.route('/health')
def health():
    """Endpoint de salud del servidor"""
    return jsonify({
        'status': 'healthy',
        'components': {
            'emotion_model': detector is not None,
            'yolo_detector': yolo_detector is not None,
            'telegram_bot': telegram_bot is not None
        }
    })

@app.route('/api/analyze', methods=['POST'])
def analyze_emotion():
    """Analiza una imagen/video para detectar emociones"""
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
            result = process_image(image, client_ip)
        elif file.filename.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
            # Procesar video
            result = process_video(file_bytes, client_ip)
        else:
            return jsonify({'success': False, 'error': 'Formato de archivo no soportado'})
        
        # Incrementar contador
        increment_analysis_count(client_ip)
        result['remaining'] = get_remaining_analyses(client_ip)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error en análisis: {e}")
        return jsonify({'success': False, 'error': str(e)})

def process_image(image, client_ip):
    """Procesa una imagen individual"""
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
        
        # Crear imagen con detecciones
        result_image = yolo_detector.draw_detections(image, dog_detections)
        
        # Agregar información de emociones
        best_detection = yolo_detector.get_best_dog_region(dog_detections)
        if best_detection:
            x, y, w, h = best_detection
            color = get_emotion_color(emotion)
            cv2.putText(result_image, f'{emotion.upper()}: {probability:.2f}', 
                       (x, y + h + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
        
        # Convertir imagen a base64
        _, buffer = cv2.imencode('.jpg', result_image)
        image_base64 = base64.b64encode(buffer).decode('utf-8')
        
        return {
            'success': True,
            'type': 'image',
            'emotion': emotion,
            'probability': float(probability),
            'predictions': {
                'happy': float(predictions[1]),
                'sad': float(predictions[3]),
                'angry': float(predictions[0]),
                'relaxed': float(predictions[2])
            },
            'image': image_base64,
            'dogs_detected': len(dog_detections)
        }
        
    except Exception as e:
        logger.error(f"Error procesando imagen: {e}")
        return {'success': False, 'error': str(e)}

def process_video(file_bytes, client_ip):
    """Procesa un video completo"""
    try:
        # Guardar video temporalmente
        temp_path = f"temp_video_{int(time.time())}.mp4"
        with open(temp_path, 'wb') as f:
            f.write(file_bytes)
        
        cap = cv2.VideoCapture(temp_path)
        
        emotions_history = []
        total_frames = 0
        frames_with_dogs = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            total_frames += 1
            
            # Procesar cada 10 frames para optimizar
            if total_frames % 10 == 0:
                dog_detections = yolo_detector.detect_dogs(frame)
                dogs_detected = yolo_detector.is_dog_detected(dog_detections)
                
                if dogs_detected:
                    frames_with_dogs += 1
                    emotion, probability, predictions = detector.predict_emotion(frame)
                    emotions_history.append({
                        'emotion': emotion,
                        'probability': float(probability),
                        'frame': total_frames
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
        
        for entry in emotions_history:
            emotion = entry['emotion']
            probability = entry['probability']
            
            if emotion not in emotion_counts:
                emotion_counts[emotion] = 0
            emotion_counts[emotion] += 1
            total_probability += probability
        
        dominant_emotion = max(emotion_counts.items(), key=lambda x: x[1])
        avg_confidence = total_probability / len(emotions_history)
        
        return {
            'success': True,
            'type': 'video',
            'total_frames': total_frames,
            'frames_analyzed': len(emotions_history),
            'frames_with_dogs': frames_with_dogs,
            'dominant_emotion': dominant_emotion[0],
            'emotion_distribution': emotion_counts,
            'average_confidence': float(avg_confidence),
            'timeline': emotions_history[:20]  # Primeros 20 resultados
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
        
        # Simular procesamiento (siempre exitoso para demo)
        time.sleep(2)  # Simular tiempo de procesamiento
        
        # Resetear contador para la IP
        client_ip = get_client_ip()
        analysis_count[client_ip] = 0  # Usuario premium sin límite
        
        # Generar código de acceso simulado
        access_code = f"PREMIUM_{int(time.time())}"
        
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
        # Generar QR code para Telegram (simulado)
        telegram_url = f"https://t.me/DogEmotionBot?start=premium_{int(time.time())}"
        
        return jsonify({
            'success': True,
            'telegram_url': telegram_url,
            'bot_username': '@DogEmotionBot',
            'instructions': [
                '1. Escanea el código QR o haz clic en el enlace',
                '2. Inicia conversación con /start',
                '3. ¡Disfruta del análisis ilimitado!'
            ]
        })
        
    except Exception as e:
        logger.error(f"Error obteniendo acceso Telegram: {e}")
        return jsonify({'success': False, 'error': str(e)})

# Eventos de WebSocket para cámara en tiempo real
@socketio.on('start_detection')
def handle_start_detection():
    """Inicia detección en tiempo real"""
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
        video_capture = cv2.VideoCapture(0)  # Cámara predeterminada
        
        if not video_capture.isOpened():
            emit('detection_error', {'error': 'No se pudo acceder a la cámara'})
            return
        
        emit('detection_started', {'status': 'success'})
        
        # Iniciar bucle de captura
        socketio.start_background_task(target=camera_loop)
        
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
    
    emit('detection_stopped', {'status': 'success'})

def camera_loop():
    """Bucle principal de captura de cámara"""
    global camera_active, video_capture
    
    while camera_active and video_capture:
        try:
            ret, frame = video_capture.read()
            if not ret:
                break
            
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
                        'confidence': float(probability)
                    }
                    
                    # Agregar texto de emoción al frame
                    best_detection = yolo_detector.get_best_dog_region(dog_detections)
                    if best_detection:
                        x, y, w, h = best_detection
                        color = get_emotion_color(emotion)
                        cv2.putText(frame_processed, f'{emotion.upper()}: {probability:.2f}', 
                                   (x, y + h + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
            else:
                frame_processed = frame
            
            # Convertir frame a base64
            _, buffer = cv2.imencode('.jpg', frame_processed)
            frame_base64 = base64.b64encode(buffer).decode('utf-8')
            
            # Emitir frame
            socketio.emit('frame_update', {'frame': frame_base64})
            
            # Emitir datos de emoción si están disponibles
            if emotion_data:
                socketio.emit('emotion_update', emotion_data)
            
            time.sleep(0.1)  # 10 FPS
            
        except Exception as e:
            logger.error(f"Error en bucle de cámara: {e}")
            break
    
    camera_active = False

@socketio.on('test_telegram')
def handle_test_telegram():
    """Envía mensaje de prueba a Telegram"""
    try:
        if telegram_bot:
            telegram_bot.send_simple_message("🧪 Mensaje de prueba desde la aplicación web")
            emit('telegram_test', {'status': 'success'})
        else:
            emit('telegram_test', {'status': 'error', 'message': 'Bot no disponible'})
    except Exception as e:
        logger.error(f"Error enviando test Telegram: {e}")
        emit('telegram_test', {'status': 'error', 'message': str(e)})

if __name__ == '__main__':
    # Inicializar modelos
    models_loaded = initialize_models()
    if not models_loaded:
        logger.warning("⚠️ Modelos no cargados completamente, funcionando en modo de desarrollo")
    
    # Crear directorio de templates si no existe
    if not os.path.exists('templates'):
        os.makedirs('templates')
    
    logger.info("🚀 Iniciando servidor web Dog Emotion AI")
    logger.info("🌐 Accede a http://localhost:5000")
    
    # Ejecutar servidor
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)