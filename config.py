# ========================================
# CONFIGURACIÓN DEL MONITOR DE EMOCIONES CANINAS
# ========================================

"""
Este archivo contiene toda la configuración necesaria para el sistema.
Modifica solo los valores que necesites personalizar.
"""

# === CONFIGURACIÓN DE TELEGRAM ===
# Token del bot oficial - ¡NO CAMBIAR ESTE VALOR!
TELEGRAM_TOKEN = "7565394500:AAEqYMlT4mQFGTlL8slsSrlrst3MZmeMzIg"



# TU CHAT ID - CAMBIA ESTE VALOR POR EL TUYO
# Obtén tu Chat ID siguiendo estas instrucciones:
# 1. Ve a Telegram y busca: @Emocionesperrunasbot
# 2. Envía /start al bot
# 3. Copia el Chat ID que te muestra
# 4. Reemplaza el valor de abajo con tu Chat ID (sin las comillas)
TELEGRAM_CHAT_ID = "1846987938"# ⚠️ CONFIGURA TU CHAT ID AQUÍ

# === CONFIGURACIÓN DE DETECCIÓN ===
# Ajusta estos valores según tus necesidades

# Umbral de confianza para YOLO (0.1 - 1.0)
# Más bajo = detecta más perros pero con menos precisión
# Más alto = detecta menos perros pero con más precisión
YOLO_CONFIDENCE_THRESHOLD = 0.60

# Intervalo entre análisis de emociones (segundos)
# Más bajo = análisis más frecuente pero consume más recursos
# Más alto = análisis menos frecuente pero más eficiente
EMOTION_ANALYSIS_INTERVAL = 2

# Número de detecciones consecutivas para activar alerta
# Más bajo = alertas más sensibles
# Más alto = alertas menos frecuentes
ALERT_THRESHOLD = 3

# Tamaño del historial emocional
EMOTION_HISTORY_SIZE = 4

# === CONFIGURACIÓN DE CÁMARA ===
# Índice de la cámara a usar (usualmente 0 para la principal)
CAMERA_INDEX = 0

# Resolución de la cámara
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
CAMERA_FPS = 30

# === CONFIGURACIÓN DE VIDEO ===
# Codec para guardar videos procesados
VIDEO_CODEC = 'mp4v'

# === CONFIGURACIÓN DE ARCHIVOS ===
# Prefijo para archivos de captura
CAPTURE_PREFIX = "captura_frame_"
ALERT_PREFIX = "alerta_"

# Formato de archivos de imagen
IMAGE_FORMAT = ".jpg"

# === MENSAJES PERSONALIZABLES ===
WAITING_MESSAGE = 'ESPERANDO DETECCION DE PERRO...'

# === CONFIGURACIÓN DE LOGGING ===
# Nivel de logging (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL = "INFO"

# Formato de logging
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'

# ========================================
# CONFIGURACIÓN AVANZADA
# ========================================

# Emojis para emociones (para Telegram)
EMOTION_EMOJIS = {
    'happy': '😊',
    'relaxed': '😌', 
    'sad': '😢',
    'angry': '😠'
}

# Colores para emociones (BGR para OpenCV)
EMOTION_COLORS = {
    'happy': (0, 255, 255),    # Amarillo
    'relaxed': (0, 255, 0),    # Verde
    'sad': (255, 0, 0),        # Azul
    'angry': (0, 0, 255)       # Rojo
}

# Recomendaciones por emoción
EMOTION_RECOMMENDATIONS = {
    'happy': "¡Tu perro se ve muy feliz! 🎉 Continúa con las actividades que lo hacen sentir bien.",
    'relaxed': "Tu perro está en un estado ideal de relajación. 😌 Mantén el ambiente tranquilo.",
    'sad': "Tu perro mostró signos de tristeza. 💙 Considera darle más atención y verificar su bienestar.",
    'angry': "Se detectó estrés o molestia. ❤️ Revisa qué podría estar causando esta reacción."
}

# ========================================
# NOTAS DE CONFIGURACIÓN
# ========================================

"""
NOTAS IMPORTANTES:

1. TELEGRAM_TOKEN: ¡NO modifiques este valor! Es el token oficial del bot.

2. TELEGRAM_CHAT_ID: Este es el único valor que DEBES cambiar.
   - Ve a @Emocionesperrunasbot en Telegram
   - Envía /start
   - Copia tu Chat ID y pégalo arriba

3. Si tienes problemas con la cámara, prueba cambiar CAMERA_INDEX a 1, 2, etc.

4. Si el sistema es muy sensible a las detecciones, aumenta YOLO_CONFIDENCE_THRESHOLD

5. Si no recibes alertas, disminuye ALERT_THRESHOLD

6. Para depuración, cambia LOG_LEVEL a "DEBUG"

COMPATIBILIDAD:
- ✅ Windows 10/11
- ✅ macOS
- ✅ Linux Ubuntu/Debian
- ✅ Python 3.8+
- ✅ Diferentes entornos virtuales
"""
