import telegram
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import asyncio
import logging
import threading
import os
from datetime import datetime
import json
import requests
import time

logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self, token=None, chat_id=None):
        # Obtener token y chat_id de parámetros o variables de entorno
        self.token = token or os.getenv('TELEGRAM_BOT_TOKEN', '7668982184:AAEXrM7xx0bDKidNOhyi6xjSNYUNRpvu61U')
        self.chat_id = chat_id or os.getenv('TELEGRAM_CHAT_ID', '1234152784')
        
        if not self.token:
            raise ValueError("❌ Token de Telegram no proporcionado. Usa el parámetro 'token' o la variable de entorno 'TELEGRAM_BOT_TOKEN'")
        
        self.application = None
        self.bot_thread = None
        self.monitoring_active = True  # Activado por defecto para alertas automáticas
        self.emotion_history = []
        self.last_status_time = 0
        
        # Estados del sistema
        self.realtime_active = False  # Estado del análisis en tiempo real
        self.realtime_thread = None   # Hilo del análisis en tiempo real
        self.current_mode = "menu"    # Modo actual: "menu", "realtime", "video"
        self.realtime_stop_flag = False  # Flag para detener el análisis
        self.camera_capture = None    # Objeto de captura de cámara
        
        # Cola thread-safe para alertas
        import queue
        self.alert_queue = queue.Queue()
        self.alert_processor_running = False
        
        # Crear bot con timeouts más agresivos
        try:
            logger.info("🔧 Creando bot con configuración optimizada...")
            self.bot = telegram.Bot(
                token=self.token,
                request=telegram.request.HTTPXRequest(
                    connection_pool_size=1,
                    read_timeout=10,
                    write_timeout=10,
                    connect_timeout=10,
                    pool_timeout=10
                )
            )
            logger.info("✅ Bot básico creado")
        except Exception as e:
            logger.error(f"❌ Error creando bot básico: {e}")
            raise e
        
        # Recomendaciones personalizadas por emoción
        self.recommendations = {
            'angry': [
                "🚨 Tu perro parece molesto. Aquí algunas recomendaciones:",
                "• Revisa si hay ruidos fuertes que lo estresen",
                "• Verifica que tenga agua fresca y comida",
                "• Dale un espacio tranquilo para calmarse",
                "• Evita forzar interacciones hasta que se calme",
                "• Si persiste, consulta con un veterinario"
            ],
            'sad': [
                "😢 Tu perro se ve triste. Te sugerimos:",
                "• Dedícale tiempo de calidad y caricias",
                "• Sácalo a pasear si es posible",
                "• Revisa si está enfermo o tiene dolor",
                "• Asegúrate de que no esté solo por mucho tiempo",
                "• Considera juguetes interactivos para estimularlo",
                "• Si la tristeza persiste, consulta al veterinario"
            ],
            'happy': [
                "😊 ¡Tu perro está feliz! Esto es genial:",
                "• Continúa con las actividades que lo hacen feliz",
                "• Es un buen momento para entrenamientos positivos",
                "• Puedes introducir nuevos juegos o juguetes"
            ],
            'relaxed': [
                "😌 Tu perro está relajado:",
                "• Es el estado ideal, continúa así",
                "• Mantén el ambiente tranquilo",
                "• Es buen momento para descanso"
            ]
        }
        
        # Inicializar bot con menú
        self._setup_bot()

    def _setup_bot(self):
        """Configurar el bot con handlers"""
        try:
            logger.info("🔧 Configurando bot de Telegram...")
            
            # Primero verificar que el bot funciona básicamente
            logger.info("🧪 Verificando bot básico...")
            try:
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    me = loop.run_until_complete(self.bot.get_me())
                    logger.info(f"✅ Bot verificado: {me.username} ({me.first_name})")
                finally:
                    loop.close()
            except Exception as verify_error:
                logger.error(f"❌ Error verificando bot: {verify_error}")
                raise verify_error
            
            # Crear application
            self.application = Application.builder().token(self.token).build()
            
            # Handlers para comandos
            self.application.add_handler(CommandHandler("start", self._start_command))
            self.application.add_handler(CommandHandler("menu", self._menu_command))
            self.application.add_handler(CommandHandler("status", self._status_command))
            self.application.add_handler(CallbackQueryHandler(self._button_callback))
            
            # Handler para videos
            from telegram.ext import MessageHandler, filters
            self.application.add_handler(MessageHandler(filters.VIDEO, self._handle_video))
            
            logger.info("✅ Handlers configurados correctamente")
            
            # Iniciar el bot en un hilo separado
            self._start_bot_thread()
            
        except Exception as e:
            logger.error(f"❌ Error configurando bot: {e}")
            logger.error(f"❌ Tipo de error: {type(e).__name__}")
            logger.error(f"❌ Detalles: {str(e)}")
            # No hacer raise para permitir que el programa continue sin Telegram
            logger.warning("⚠️ Continuando sin funcionalidad completa de Telegram")

    def _start_bot_thread(self):
        """Iniciar el bot en un hilo separado"""
        def run_bot():
            try:
                logger.info("🚀 Iniciando hilo del bot...")
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                logger.info("🔄 Loop de evento creado")
                
                # Configurar el bot para polling más controlado
                logger.info("🔍 Iniciando polling de Telegram...")
                self.application.run_polling(
                    drop_pending_updates=True,
                    timeout=10
                )
                logger.info("✅ Polling iniciado exitosamente")
            except Exception as e:
                logger.error(f"❌ Error ejecutando bot: {e}")
                logger.error(f"❌ Tipo de error: {type(e).__name__}")
                logger.error(f"❌ Detalles del error: {str(e)}")
            finally:
                try:
                    loop.close()
                    logger.info("🔄 Loop cerrado")
                except Exception as loop_error:
                    logger.error(f"Error cerrando loop: {loop_error}")
        
        try:
            self.bot_thread = threading.Thread(target=run_bot, daemon=True)
            self.bot_thread.start()
            logger.info("🤖 Bot de Telegram iniciado con menú interactivo")
        except Exception as thread_error:
            logger.error(f"❌ Error iniciando hilo del bot: {thread_error}")

    async def _start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /start"""
        welcome_text = (
            "🐕 **¡Bienvenido al Monitor de Emociones Caninas!**\n\n"
            "Tu asistente personal para el bienestar de tu mascota.\n\n"
            "Usa /menu para ver todas las opciones disponibles."
        )
        await update.message.reply_text(welcome_text, parse_mode='Markdown')
        await self._menu_command(update, context)

    async def _menu_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Mostrar menú principal con nuevas opciones"""
        keyboard = [
            [InlineKeyboardButton("📹 Análisis en Tiempo Real", callback_data="realtime_analysis")],
            [InlineKeyboardButton("🎬 Analizar Video", callback_data="video_analysis")],
            [InlineKeyboardButton("📊 Estado Actual", callback_data="status")],
            [InlineKeyboardButton("📈 Resumen del Día", callback_data="summary")],
            [InlineKeyboardButton("🔔 Activar Monitoreo", callback_data="monitor_on")],
            [InlineKeyboardButton("🔕 Pausar Monitoreo", callback_data="monitor_off")],
            [InlineKeyboardButton("💡 Consejos Generales", callback_data="tips")],
            [InlineKeyboardButton("🧹 Limpiar Chat", callback_data="clear_chat")],
            [InlineKeyboardButton("❓ Ayuda", callback_data="help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        menu_text = (
            "🎛️ **MENÚ PRINCIPAL**\n\n"
            "Selecciona una opción para gestionar el monitoreo de tu mascota:"
        )
        
        if update.message:
            await update.message.reply_text(menu_text, reply_markup=reply_markup, parse_mode='Markdown')
        elif update.callback_query:
            # Enviar mensaje nuevo cuando se llama desde callback
            await update.callback_query.message.reply_text(menu_text, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            # Fallback: intentar con callback_query si no hay message
            await update.callback_query.edit_message_text(menu_text, reply_markup=reply_markup, parse_mode='Markdown')

    async def _status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /status"""
        status_text = self._get_current_status()
        await update.message.reply_text(status_text, parse_mode='Markdown')

    async def _button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Manejar clics en botones"""
        query = update.callback_query
        await query.answer()
        
        # Botón para mostrar menú
        if query.data == "show_menu":
            await self._menu_command(update, context)
            return
            
        # Análisis en tiempo real
        elif query.data == "realtime_analysis":
            await self._handle_realtime_analysis(update, context)
            
        # Análisis de video
        elif query.data == "video_analysis":
            await self._handle_video_analysis_request(update, context)
            
        elif query.data == "status":
            status_text = self._get_current_status()
            keyboard = [[InlineKeyboardButton("🏠 Regresar al Menú", callback_data="show_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.reply_text(status_text, reply_markup=reply_markup, parse_mode='Markdown')
            
        elif query.data == "summary":
            summary_text = self._get_daily_summary()
            keyboard = [[InlineKeyboardButton("🏠 Regresar al Menú", callback_data="show_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.reply_text(summary_text, reply_markup=reply_markup, parse_mode='Markdown')
            
        elif query.data == "monitor_on":
            self.monitoring_active = True
            keyboard = [[InlineKeyboardButton("🏠 Regresar al Menú", callback_data="show_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.reply_text(
                "🔔 **Monitoreo Activado**\n\n"
                "✅ Ahora recibirás alertas automáticas sobre el estado emocional de tu mascota.\n"
                "✅ Actualizaciones periódicas cada 30 minutos\n"
                "✅ Alertas inmediatas ante patrones preocupantes\n\n"
                "El sistema está monitoreando activamente a tu mascota.",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
        elif query.data == "monitor_off":
            self.monitoring_active = False
            keyboard = [[InlineKeyboardButton("🏠 Regresar al Menú", callback_data="show_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            # Enviar mensaje nuevo en lugar de editar
            await query.message.reply_text(
                "🔕 **Monitoreo Pausado**\n\n"
                "❌ Las alertas automáticas están desactivadas\n"
                "❌ No recibirás actualizaciones periódicas\n"
                "❌ No se enviarán alertas de patrones preocupantes\n\n"
                "El análisis continúa pero sin notificaciones automáticas.\n"
                "Puedes consultar el estado manualmente cuando gustes.",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
        elif query.data == "tips":
            tips_text = self._get_general_tips()
            keyboard = [[InlineKeyboardButton("� Mostrar Menú", callback_data="show_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            # Enviar mensaje nuevo en lugar de editar
            await query.message.reply_text(tips_text, reply_markup=reply_markup, parse_mode='Markdown')
            
        elif query.data == "help":
            help_text = (
                "❓ **AYUDA**\n\n"
                "**Comandos disponibles:**\n"
                "• /start - Iniciar el bot\n"
                "• /menu - Mostrar menú principal\n"
                "• /status - Estado actual de tu mascota\n\n"
                "**Funciones:**\n"
                "• Monitoreo en tiempo real\n"
                "• Alertas automáticas\n"
                "• Resúmenes diarios\n"
                "• Recomendaciones personalizadas\n\n"
                "**Estado del Monitoreo:**\n"
                f"🔔 Monitoreo: {'✅ ACTIVO' if self.monitoring_active else '❌ PAUSADO'}\n\n"
                "El sistema analiza las emociones de tu mascota y te mantiene informado."
            )
            keyboard = [[InlineKeyboardButton("� Mostrar Menú", callback_data="show_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            # Enviar mensaje nuevo en lugar de editar
            await query.message.reply_text(help_text, reply_markup=reply_markup, parse_mode='Markdown')
            
        elif query.data == "clear_chat":
            # Confirmar antes de limpiar
            keyboard = [
                [InlineKeyboardButton("✅ Sí, limpiar", callback_data="confirm_clear")],
                [InlineKeyboardButton("❌ Cancelar", callback_data="show_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            # Enviar mensaje nuevo en lugar de editar
            await query.message.reply_text(
                "🧹 **Limpiar Chat**\n\n"
                "⚠️ Esta acción eliminará todos los mensajes del bot en este chat.\n"
                "¿Estás seguro de que quieres continuar?",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
        elif query.data == "confirm_clear":
            try:
                # Intentar eliminar mensajes recientes
                await self._clear_chat_messages(query)
                # Enviar mensaje nuevo en lugar de editar
                await query.message.reply_text(
                    "🧹 **Chat Limpiado**\n\n"
                    "✅ Se han eliminado los mensajes del bot.\n"
                    "El historial de análisis se mantiene intacto.\n\n"
                    "Usa /menu para continuar.",
                    parse_mode='Markdown'
                )
            except Exception as e:
                keyboard = [[InlineKeyboardButton("� Mostrar Menú", callback_data="show_menu")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                # Enviar mensaje nuevo en lugar de editar
                await query.message.reply_text(
                    "❌ **Error al limpiar**\n\n"
                    "No se pudieron eliminar todos los mensajes.\n"
                    "Esto puede deberse a limitaciones de Telegram.\n\n"
                    "Puedes eliminar mensajes manualmente si es necesario.",
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
            
        # Nuevos handlers para análisis en tiempo real
        elif query.data == "start_realtime":
            await self._start_realtime_analysis(update, context)
            
        elif query.data == "pause_realtime":
            await self._pause_realtime_analysis()
            keyboard = [
                [InlineKeyboardButton("▶️ Reanudar", callback_data="resume_realtime")],
                [InlineKeyboardButton("⏹️ Detener", callback_data="stop_realtime")],
                [InlineKeyboardButton("🏠 Menú", callback_data="show_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.reply_text(
                "⏸️ **ANÁLISIS PAUSADO**\n\n"
                "⏯️ El análisis en tiempo real está pausado\n"
                "📊 Los datos anteriores se mantienen\n\n"
                "Puedes reanudar cuando gustes.",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
        elif query.data == "resume_realtime":
            await self._resume_realtime_analysis(update, context)
            
        elif query.data == "stop_realtime":
            await self._stop_realtime_analysis(update, context)
            
        elif query.data == "switch_to_video":
            await self._pause_realtime_analysis()
            await self._handle_video_analysis_request(update, context)

    async def _handle_realtime_analysis(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Manejar el análisis en tiempo real"""
        query = update.callback_query
        
        if self.realtime_active:
            # Si ya está activo, mostrar opciones de control
            keyboard = [
                [InlineKeyboardButton("⏸️ Pausar Análisis", callback_data="pause_realtime")],
                [InlineKeyboardButton("⏹️ Detener Análisis", callback_data="stop_realtime")],
                [InlineKeyboardButton("🎬 Cambiar a Video", callback_data="switch_to_video")],
                [InlineKeyboardButton("🏠 Regresar al Menú", callback_data="show_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.message.reply_text(
                "📹 **ANÁLISIS EN TIEMPO REAL ACTIVO**\n\n"
                "✅ El sistema está analizando a tu mascota en vivo\n"
                "📊 Recibes actualizaciones en tiempo real\n"
                "🔔 Alertas automáticas activadas\n\n"
                "**Opciones disponibles:**",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        else:
            # Si no está activo, iniciar
            keyboard = [
                [InlineKeyboardButton("🚀 Iniciar Análisis", callback_data="start_realtime")],
                [InlineKeyboardButton("🎬 Mejor Analizar Video", callback_data="video_analysis")],
                [InlineKeyboardButton("🏠 Regresar al Menú", callback_data="show_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.message.reply_text(
                "📹 **ANÁLISIS EN TIEMPO REAL**\n\n"
                "🎯 **Características:**\n"
                "• Análisis continuo usando la cámara\n"
                "• Detección inmediata de emociones\n"
                "• Alertas en tiempo real\n"
                "• Recomendaciones instantáneas\n\n"
                "⚠️ **Requisitos:**\n"
                "• Cámara web conectada\n"
                "• Aplicación principal ejecutándose\n"
                "• Tu perro debe estar visible\n\n"
                "🔄 **Nota:** El análisis se ejecuta desde la aplicación principal.",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )

    async def _handle_video_analysis_request(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Manejar solicitud de análisis de video"""
        query = update.callback_query
        
        # Si hay análisis en tiempo real activo, pausarlo
        if self.realtime_active:
            await self._pause_realtime_analysis()
            
        keyboard = [
            [InlineKeyboardButton("📹 Cambiar a Tiempo Real", callback_data="realtime_analysis")],
            [InlineKeyboardButton("🏠 Regresar al Menú", callback_data="show_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.reply_text(
            "🎬 **ANÁLISIS DE VIDEO**\n\n"
            "📎 **Envía un video de tu mascota** y lo analizaré automáticamente.\n\n"
            "📋 **Requisitos del video:**\n"
            "• Formato: MP4, AVI, MOV\n"
            "• Duración: Máximo 2 minutos\n"
            "• Tamaño: Máximo 20MB\n"
            "• Tu perro debe ser visible claramente\n\n"
            "🔄 **Proceso:**\n"
            "1️⃣ Envía el video como archivo adjunto\n"
            "2️⃣ Procesaré automáticamente el video\n"
            "3️⃣ Te enviaré el video con análisis superpuesto\n"
            "4️⃣ Recibirás un resumen completo con recomendaciones\n\n"
            "📤 **¡Adelante, envía tu video ahora!**",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    async def _start_realtime_analysis(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Iniciar análisis en tiempo real"""
        try:
            logger.info("🚀 Iniciando análisis en tiempo real desde Telegram...")
            
            # Verificar si ya está corriendo
            if self.realtime_active:
                keyboard = [
                    [InlineKeyboardButton("⏸️ Pausar", callback_data="pause_realtime")],
                    [InlineKeyboardButton("⏹️ Detener", callback_data="stop_realtime")],
                    [InlineKeyboardButton("🏠 Menú", callback_data="show_menu")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.callback_query.message.reply_text(
                    "⚠️ **ANÁLISIS YA ACTIVO**\n\n"
                    "El análisis en tiempo real ya está ejecutándose.\n"
                    "Puedes pausarlo o detenerlo si lo necesitas.",
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
                return
            
            # Cambiar estado
            self.realtime_active = True
            self.current_mode = "realtime"
            self.realtime_stop_flag = False
            
            # Iniciar hilo de análisis en tiempo real
            import threading
            self.realtime_thread = threading.Thread(
                target=self._realtime_analysis_worker,
                args=(update.callback_query.message.chat_id,)
            )
            self.realtime_thread.daemon = True
            self.realtime_thread.start()
            
            keyboard = [
                [InlineKeyboardButton("⏸️ Pausar", callback_data="pause_realtime")],
                [InlineKeyboardButton("⏹️ Detener", callback_data="stop_realtime")],
                [InlineKeyboardButton("🎬 Cambiar a Video", callback_data="switch_to_video")],
                [InlineKeyboardButton("🏠 Menú", callback_data="show_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.callback_query.message.reply_text(
                "🚀 **ANÁLISIS EN TIEMPO REAL INICIADO**\n\n"
                "✅ Cámara activada\n"
                "📹 Analizando video en vivo\n"
                "🔔 Alertas automáticas activadas\n\n"
                "💡 **Tip:** Mantén a tu mascota visible en la cámara para mejores resultados.\n\n"
                "El análisis se está ejecutando en segundo plano.",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"❌ Error iniciando análisis en tiempo real: {e}")
            await update.callback_query.message.reply_text(
                "❌ **Error iniciando análisis**\n\n"
                "No se pudo iniciar el análisis en tiempo real.\n"
                "Verifica que la cámara esté disponible.",
                parse_mode='Markdown'
            )

    def _realtime_analysis_worker(self, chat_id):
        """Worker que ejecuta el análisis en tiempo real usando la lógica probada"""
        try:
            logger.info("📹 Iniciando worker de análisis en tiempo real...")
            
            # Importar OpenCV al inicio
            import cv2
            
            # Encontrar cámara disponible
            camera_index = self._find_available_camera()
            if camera_index is None:
                logger.error("❌ No se encontró cámara disponible")
                self._send_error_to_chat(chat_id, "❌ No se encontró cámara disponible")
                return
            
            # Inicializar componentes usando la misma lógica que funciona
            logger.info("🧠 Cargando modelos de IA...")
            try:
                from .cam_utils import EmotionDetector
                from .yolo_dog_detector import YoloDogDetector
            except ImportError:
                # Intento alternativo si las importaciones relativas fallan
                import sys
                import os
                sys.path.append(os.path.dirname(os.path.dirname(__file__)))
                from utils.cam_utils import EmotionDetector
                from utils.yolo_dog_detector import YoloDogDetector
            
            detector = EmotionDetector("modelo/mejor_modelo_83.h5")
            yolo_detector = YoloDogDetector(confidence_threshold=0.60)
            
            # Abrir cámara usando la misma configuración que funciona
            self.camera_capture = cv2.VideoCapture(camera_index)
            self.camera_capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.camera_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.camera_capture.set(cv2.CAP_PROP_FPS, 30)
            
            if not self.camera_capture.isOpened():
                logger.error("❌ No se pudo abrir la cámara")
                self._send_error_to_chat(chat_id, "❌ No se pudo abrir la cámara")
                return
            
            logger.info("✅ Análisis en tiempo real iniciado correctamente")
            self._send_status_to_chat(chat_id, "✅ **CÁMARA ACTIVADA**\n\nEl análisis en tiempo real está funcionando.\n\n🖥️ **Una ventana de la cámara se abrirá en tu PC**")
            
            # Variables de seguimiento usando la misma lógica que funciona
            emotion_history = []
            cooldown_time = 2  # Mismo que en main.py
            last_analysis_time = time.time()
            frame_count = 0
            last_alert_time = 0
            last_update_time = time.time()
            
            # Configurar ventana de OpenCV
            window_name = "🐕 Dog Emotion Monitor - Análisis en Tiempo Real"
            cv2.namedWindow(window_name, cv2.WINDOW_AUTOSIZE)
            cv2.moveWindow(window_name, 100, 100)
            
            logger.info("🖥️ Ventana de cámara abierta - presiona 'q' para pausar o 'ESC' para detener")
            logger.info("🎮 CONTROLES: Q o ESC=Salir | Telegram=Control remoto")
            
            while self.realtime_active and not self.realtime_stop_flag:
                ret, frame = self.camera_capture.read()
                if not ret:
                    logger.error("Error capturando frame")
                    continue
                
                current_time = time.time()
                frame_count += 1
                
                # PASO 1: Detectar perros con YOLO (usando la lógica que funciona)
                dog_detections = yolo_detector.detect_dogs(frame)
                dogs_detected = yolo_detector.is_dog_detected(dog_detections)
                
                # PASO 2: Dibujar detecciones de YOLO solamente (como en main.py)
                frame = yolo_detector.draw_detections(frame, dog_detections)
                
                # PASO 3: Solo analizar emociones SI hay perros detectados
                if dogs_detected and current_time - last_analysis_time >= cooldown_time:
                    try:
                        logger.info(f"🐕 Analizando emociones... (perro detectado)")
                        emotion, prob, preds = detector.predict_emotion(frame)
                        
                        logger.info(f"🎯 Emoción detectada: {emotion.upper()} ({prob:.3f})")
                        
                        # Determinar color según emoción
                        color = (0, 255, 0)  # Verde por defecto
                        if emotion in ['angry', 'sad']:
                            color = (0, 0, 255)  # Rojo para emociones negativas
                        elif emotion == 'happy':
                            color = (0, 255, 0)  # Verde para happy
                        elif emotion == 'relaxed':
                            color = (255, 255, 0)  # Amarillo para relaxed
                        
                        # Mostrar resultado en frame
                        cv2.putText(frame, f"Emotion: {emotion.upper()}", (10, 30), 
                                  cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
                        cv2.putText(frame, f"Confidence: {prob:.3f}", (10, 60), 
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
                        
                        # Gestionar historial de emociones
                        emotion_history.append((emotion, prob, current_time))
                        if len(emotion_history) > 50:  # Mantener últimas 50 detecciones
                            emotion_history.pop(0)
                        
                        # Enviar alerta si es necesario (cada 30 segundos máximo)
                        if current_time - last_alert_time > 30:
                            if emotion in ['angry', 'sad'] and prob > 0.7:
                                self._send_emotion_alert(chat_id, emotion, prob)
                                last_alert_time = current_time
                        
                        # Enviar actualización cada 60 segundos
                        if current_time - last_update_time > 60:
                            emotion_counts = {'happy': 0, 'sad': 0, 'angry': 0, 'relaxed': 0}
                            for emo, _, _ in emotion_history:
                                emotion_counts[emo] += 1
                            self._send_realtime_update(chat_id, emotion_counts, frame_count)
                            last_update_time = current_time
                        
                        last_analysis_time = current_time
                        
                    except Exception as e:
                        logger.debug(f"Error analizando emoción: {e}")
                
                # Agregar información adicional en la pantalla
                cv2.putText(frame, f"Frame: {frame_count}", (10, frame.shape[0] - 40), 
                          cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                cv2.putText(frame, f"Dogs: {'YES' if dogs_detected else 'NO'}", (10, frame.shape[0] - 20), 
                          cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0) if dogs_detected else (128, 128, 128), 1)
                
                # Controles
                cv2.putText(frame, "Q=Pause | ESC=Stop | Telegram=Remote", (10, frame.shape[0] - 5), 
                          cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
                
                # Mostrar frame
                cv2.imshow(window_name, frame)
                
                # Manejar teclas
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q') or key == ord('Q'):
                    # Pausar análisis
                    logger.info("⏸️ Análisis pausado por tecla 'Q'")
                    self.realtime_active = False
                    self.current_mode = "paused"
                    break
                elif key == 27:  # ESC
                    # Detener análisis
                    logger.info("⏹️ Análisis detenido por tecla 'ESC'")
                    self.realtime_stop_flag = True
                    break
            
            # Limpiar al terminar
            cv2.destroyAllWindows()
            if self.camera_capture:
                self.camera_capture.release()
                self.camera_capture = None
                
            logger.info("🔚 Análisis en tiempo real terminado - ventana cerrada")
            
        except Exception as e:
            logger.error(f"❌ Error en worker de análisis: {e}")
            self._send_error_to_chat(chat_id, f"❌ Error en análisis: {str(e)[:50]}...")
        finally:
            # Asegurar que se cierre todo
            cv2.destroyAllWindows()
            if self.camera_capture:
                self.camera_capture.release()
                self.camera_capture = None
            self.realtime_active = False
            self.current_mode = "menu"

    async def _resume_realtime_analysis(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Reanudar análisis en tiempo real"""
        if self.realtime_active:
            keyboard = [[InlineKeyboardButton("🏠 Regresar al Menú", callback_data="show_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.callback_query.message.reply_text(
                "⚠️ El análisis ya está activo",
                reply_markup=reply_markup
            )
            return
        
        # Verificar cámara disponible
        camera_index = self._find_available_camera()
        if camera_index is None:
            keyboard = [[InlineKeyboardButton("🏠 Regresar al Menú", callback_data="show_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.callback_query.message.reply_text(
                "❌ **ERROR DE CÁMARA**\n\n"
                "No se pudo detectar ninguna cámara disponible.\n"
                "Por favor verifica que:\n"
                "• La cámara esté conectada\n"
                "• No esté siendo usada por otra aplicación\n"
                "• Los drivers estén instalados correctamente",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            return
        
        # Reiniciar análisis
        await self._start_realtime_analysis(update, context, chat_id=update.effective_chat.id)

    def _find_available_camera(self):
        """Encuentra la primera cámara disponible"""
        import cv2
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

    def _send_error_to_chat(self, chat_id, message):
        """Enviar mensaje de error a un chat específico"""
        try:
            import requests
            url = f"https://api.telegram.org/bot{self.token}/sendMessage"
            data = {
                'chat_id': chat_id,
                'text': message,
                'parse_mode': 'Markdown'
            }
            requests.post(url, json=data, timeout=10)
        except Exception as e:
            logger.error(f"Error enviando mensaje de error: {e}")

    def _send_status_to_chat(self, chat_id, message):
        """Enviar mensaje de estado a un chat específico"""
        try:
            import requests
            url = f"https://api.telegram.org/bot{self.token}/sendMessage"
            data = {
                'chat_id': chat_id,
                'text': message,
                'parse_mode': 'Markdown'
            }
            requests.post(url, json=data, timeout=10)
        except Exception as e:
            logger.error(f"Error enviando mensaje de estado: {e}")

    def _send_emotion_alert(self, chat_id, emotion, confidence):
        """Enviar alerta de emoción preocupante"""
        try:
            emotion_messages = {
                'angry': f"⚠️ **ALERTA: ESTRÉS DETECTADO**\n\nTu mascota muestra signos de molestia (confianza: {confidence:.1%})\n\n🔍 **Revisa:**\n• Ruidos fuertes\n• Cambios en el entorno\n• Necesidades básicas",
                'sad': f"💙 **ALERTA: TRISTEZA DETECTADA**\n\nTu mascota parece triste (confianza: {confidence:.1%})\n\n💡 **Considera:**\n• Dedicar más tiempo de calidad\n• Actividades estimulantes\n• Verificar salud general"
            }
            
            message = emotion_messages.get(emotion, f"🔔 Emoción detectada: {emotion} ({confidence:.1%})")
            
            import requests
            url = f"https://api.telegram.org/bot{self.token}/sendMessage"
            data = {
                'chat_id': chat_id,
                'text': message,
                'parse_mode': 'Markdown'
            }
            requests.post(url, json=data, timeout=10)
            logger.info(f"🚨 Alerta enviada: {emotion} - {confidence:.1%}")
        except Exception as e:
            logger.error(f"Error enviando alerta: {e}")

    def _send_realtime_update(self, chat_id, emotion_counts, frame_count):
        """Enviar actualización del análisis en tiempo real"""
        try:
            total_detections = sum(emotion_counts.values())
            if total_detections == 0:
                message = "📊 **ACTUALIZACIÓN**\n\n🔍 Buscando a tu mascota...\nAsegúrate de que esté visible en la cámara."
            else:
                dominant_emotion = max(emotion_counts.items(), key=lambda x: x[1])
                
                message = f"📊 **ACTUALIZACIÓN EN TIEMPO REAL**\n\n"
                message += f"🎯 Emoción predominante: **{dominant_emotion[0].upper()}**\n"
                message += f"📈 Total detecciones: {total_detections}\n"
                message += f"🎬 Frames procesados: {frame_count}\n\n"
                
                message += "📊 **Distribución:**\n"
                for emotion, count in emotion_counts.items():
                    if count > 0:
                        percentage = (count / total_detections) * 100
                        message += f"• {emotion.upper()}: {count} ({percentage:.0f}%)\n"
            
            import requests
            url = f"https://api.telegram.org/bot{self.token}/sendMessage"
            data = {
                'chat_id': chat_id,
                'text': message,
                'parse_mode': 'Markdown'
            }
            requests.post(url, json=data, timeout=10)
            logger.info("📊 Actualización de tiempo real enviada")
        except Exception as e:
            logger.error(f"Error enviando actualización: {e}")

    async def _pause_realtime_analysis(self):
        """Pausar análisis en tiempo real"""
        self.realtime_active = False
        self.current_mode = "paused"
        logger.info("⏸️ Análisis en tiempo real pausado")

    async def _stop_realtime_analysis(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Detener análisis en tiempo real"""
        logger.info("⏹️ Deteniendo análisis en tiempo real...")
        
        # Cambiar flags
        self.realtime_active = False
        self.realtime_stop_flag = True
        self.current_mode = "menu"
        
        # Cerrar cámara si está abierta
        if self.camera_capture:
            self.camera_capture.release()
            self.camera_capture = None
        
        # Esperar que termine el hilo
        if self.realtime_thread and self.realtime_thread.is_alive():
            self.realtime_thread.join(timeout=2)
        
        keyboard = [[InlineKeyboardButton("🏠 Regresar al Menú", callback_data="show_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.callback_query.message.reply_text(
            "⏹️ **ANÁLISIS DETENIDO**\n\n"
            "✅ El análisis en tiempo real ha sido detenido\n"
            "📹 Cámara liberada\n"
            "📊 Los datos recopilados han sido guardados\n\n"
            "Puedes reiniciar el análisis cuando gustes.",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
        logger.info("✅ Análisis en tiempo real detenido correctamente")

    def _get_current_status(self):
        """Obtener estado actual"""
        if not self.emotion_history:
            return (
                "📊 **ESTADO ACTUAL**\n\n"
                "🔍 Aún no hay datos de análisis\n"
                "Asegúrate de que el sistema esté detectando a tu mascota.\n\n"
                f"🔔 Monitoreo: {'Activo' if self.monitoring_active else 'Pausado'}"
            )
        
        last_emotion = self.emotion_history[-1] if self.emotion_history else "Sin datos"
        recent_emotions = self.emotion_history[-5:] if len(self.emotion_history) >= 5 else self.emotion_history
        
        # Contar emociones recientes
        emotion_counts = {}
        for emotion in recent_emotions:
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
        
        status_text = (
            f"📊 **ESTADO ACTUAL**\n\n"
            f"🎯 Última emoción: **{last_emotion.upper()}**\n"
            f"📈 Análisis recientes: {len(recent_emotions)}\n\n"
            f"**Distribución reciente:**\n"
        )
        
        for emotion, count in emotion_counts.items():
            percentage = (count / len(recent_emotions)) * 100
            emoji = {"happy": "😊", "sad": "😢", "angry": "😠", "relaxed": "😌"}.get(emotion, "🐕")
            status_text += f"{emoji} {emotion.capitalize()}: {count} ({percentage:.0f}%)\n"
        
        status_text += f"\n🔔 Monitoreo: {'✅ ACTIVO' if self.monitoring_active else '❌ PAUSADO'}"
        status_text += f"\n⏰ Última actualización: {self._get_current_time()}"
        
        if not self.monitoring_active:
            status_text += f"\n\n💡 *Activa el monitoreo desde el menú para recibir alertas automáticas*"
        
        return status_text

    def _get_daily_summary(self):
        """Obtener resumen del día"""
        if not self.emotion_history:
            return (
                "📈 **RESUMEN DEL DÍA**\n\n"
                "📊 Sin datos suficientes para generar resumen\n"
                "El sistema comenzará a recopilar datos una vez que detecte a tu mascota."
            )
        
        # Contar todas las emociones
        emotion_counts = {}
        for emotion in self.emotion_history:
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
        
        total = len(self.emotion_history)
        dominant_emotion = max(emotion_counts, key=emotion_counts.get)
        
        summary_text = (
            f"📈 **RESUMEN DEL DÍA**\n\n"
            f"📊 Total de análisis: **{total}**\n"
            f"🎯 Emoción dominante: **{dominant_emotion.upper()}**\n\n"
            f"**Distribución completa:**\n"
        )
        
        for emotion, count in sorted(emotion_counts.items()):
            percentage = (count / total) * 100
            emoji = {"happy": "😊", "sad": "😢", "angry": "😠", "relaxed": "😌"}.get(emotion, "🐕")
            summary_text += f"{emoji} {emotion.capitalize()}: {count} análisis ({percentage:.1f}%)\n"
        
        # Agregar recomendación basada en emoción dominante
        summary_text += f"\n**Recomendación del día:**\n"
        recommendations = self.get_recommendations(dominant_emotion)
        summary_text += recommendations[0] if recommendations else "Continúa monitoreando"
        
        return summary_text

    def _get_general_tips(self):
        """Obtener consejos generales"""
        return (
            "💡 **CONSEJOS GENERALES PARA TU MASCOTA**\n\n"
            "🏃‍♂️ **Ejercicio Regular:**\n"
            "• Paseos diarios adaptados a la edad y raza\n"
            "• Juegos interactivos en casa\n\n"
            "🥗 **Alimentación:**\n"
            "• Horarios regulares de comida\n"
            "• Agua fresca siempre disponible\n\n"
            "❤️ **Bienestar Emocional:**\n"
            "• Rutinas consistentes\n"
            "• Tiempo de calidad juntos\n"
            "• Ambiente tranquilo para descansar\n\n"
            "🏥 **Salud:**\n"
            "• Visitas regulares al veterinario\n"
            "• Atención a cambios de comportamiento\n\n"
            "📱 Este sistema te ayuda a monitorear el estado emocional y detectar patrones que podrían requerir atención."
        )

    def get_recommendations(self, emotion):
        """Obtiene recomendaciones específicas para cada emoción"""
        return self.recommendations.get(emotion, ["Monitoreando el estado de tu mascota..."])

    def update_emotion_history(self, emotion):
        """Actualizar historial de emociones"""
        self.emotion_history.append(emotion)
        # Mantener solo las últimas 200 emociones para análisis más completo
        if len(self.emotion_history) > 200:
            self.emotion_history.pop(0)

    def send_image_with_caption(self, image_path, caption):
        """Envía una imagen con texto usando requests"""
        try:
            logger.info(f"📸 Enviando imagen: {image_path}")
            
            url = f"https://api.telegram.org/bot{self.token}/sendPhoto"
            
            with open(image_path, 'rb') as photo:
                files = {'photo': photo}
                data = {
                    'chat_id': self.chat_id,
                    'caption': caption,
                    'parse_mode': 'Markdown'
                }
                
                response = requests.post(url, files=files, data=data, timeout=15)
                
                if response.status_code == 200:
                    logger.info("✅ Imagen enviada exitosamente")
                    return True
                else:
                    logger.error(f"❌ Error enviando imagen: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Error enviando imagen: {e}")
            return False

    def send_alert(self, emotion, probability, image_path=None):
        """Envía alerta con recomendaciones personalizadas"""
        try:
            logger.info(f"🚨 SEND_ALERT LLAMADO: emotion={emotion}, prob={probability:.3f}, image_path={image_path}")
            logger.info(f"🔍 Estado del monitoreo: {self.monitoring_active}")
            
            # Solo enviar si el monitoreo está activo
            if not self.monitoring_active:
                logger.warning("⚠️ Alerta no enviada - Monitoreo pausado")
                return False
                
            logger.info("✅ Monitoreo activo - Procesando alerta...")
            
            recommendations = self.get_recommendations(emotion)
            
            # Crear mensaje personalizado
            message = f"🐕 **ALERTA DE COMPORTAMIENTO**\n\n"
            message += f"Emoción detectada: **{emotion.upper()}** ({probability:.2f})\n"
            message += f"Detectado repetidamente en los últimos análisis.\n\n"
            message += "\n".join(recommendations)
            message += f"\n\n📊 Confianza: {probability*100:.1f}%"
            message += f"\n⏰ Hora: {self._get_current_time()}"
            
            # PRIORIDAD 1: Si hay imagen, enviarla con el mensaje completo
            if image_path and os.path.exists(image_path):
                logger.info("📸 Enviando alerta CON IMAGEN...")
                success = self.send_image_with_caption(image_path, message)
                
                if success:
                    logger.info("🎉 Alerta con imagen enviada exitosamente")
                    return True
                else:
                    logger.warning("⚠️ Falló envío con imagen, enviando mensaje sin imagen...")
            
            # PRIORIDAD 2: Enviar mensaje usando método directo (más confiable)
            logger.info("📝 Enviando alerta con método directo...")
            try:
                url = f"https://api.telegram.org/bot{self.token}/sendMessage"
                data = {
                    'chat_id': self.chat_id,
                    'text': message,
                    'parse_mode': 'Markdown'
                }
                
                response = requests.post(url, json=data, timeout=10)
                
                if response.status_code == 200:
                    logger.info("🎉 Alerta enviada exitosamente con método directo")
                    return True
                else:
                    logger.error(f"❌ Error HTTP en método directo: {response.status_code}")
                    raise Exception(f"HTTP Error: {response.status_code}")
                    
            except Exception as direct_error:
                logger.error(f"❌ Error en método directo: {direct_error}")
                
                # Respaldo ultra-simple
                logger.info("📱 Intentando mensaje de respaldo...")
                fallback_msg = f"🚨 ALERTA: Tu perro está {emotion.upper()} (confianza: {probability:.2f})"
                
                try:
                    fallback_data = {
                        'chat_id': self.chat_id,
                        'text': fallback_msg
                    }
                    
                    fallback_response = requests.post(url, json=fallback_data, timeout=10)
                    
                    if fallback_response.status_code == 200:
                        logger.info("📱 Mensaje de respaldo enviado exitosamente")
                        return True
                    else:
                        logger.error("❌ Falló incluso el mensaje de respaldo")
                        return False
                        
                except Exception as fallback_error:
                    logger.error(f"❌ Error en respaldo: {fallback_error}")
                    return False
                
        except Exception as e:
            logger.error(f"❌ Error general enviando alerta: {e}")
            return False

    def send_status_update(self, emotion_history=None):
        """Envía un resumen del estado emocional reciente"""
        try:
            if not self.monitoring_active:
                return
                
            history_to_use = emotion_history or self.emotion_history
            if not history_to_use:
                return
                
            # Contar emociones
            emotion_counts = {}
            for emotion in history_to_use:
                emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
            
            message = "📊 **ACTUALIZACIÓN DE ESTADO**\n\n"
            for emotion, count in emotion_counts.items():
                percentage = (count / len(history_to_use)) * 100
                emoji = {"happy": "😊", "sad": "😢", "angry": "😠", "relaxed": "😌"}.get(emotion, "🐕")
                message += f"{emoji} {emotion.capitalize()}: {count} veces ({percentage:.1f}%)\n"
            
            message += f"\n📈 Total de análisis: {len(history_to_use)}"
            message += f"\n⏰ Actualización: {self._get_current_time()}"
            
            # Usar método asíncrono manejado de forma síncrona
            import asyncio
            import threading
            
            # Variable para almacenar el resultado
            status_result = {'success': False, 'error': None}
            
            async def _send_status_async():
                """Función async interna para envío de estado"""
                try:
                    await self.bot.send_message(
                        chat_id=self.chat_id,
                        text=message,
                        parse_mode='Markdown'
                    )
                    logger.info("Resumen de estado enviado")
                    status_result['success'] = True
                except Exception as e:
                    status_result['error'] = e
                    logger.error(f"❌ Error en envío async de estado: {e}")
            
            def _run_status():
                """Ejecutar envío de estado en nuevo event loop"""
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(_send_status_async())
                except Exception as e:
                    status_result['error'] = e
                    logger.error(f"❌ Error en loop de estado: {e}")
                finally:
                    try:
                        loop.close()
                    except:
                        pass
            
            # Ejecutar en hilo separado
            status_thread = threading.Thread(target=_run_status)
            status_thread.start()
            status_thread.join(timeout=10)  # Timeout de 10 segundos
            
            if status_thread.is_alive():
                logger.error("❌ Timeout enviando estado")
                return
            
            if not status_result['success'] and status_result['error']:
                raise status_result['error']
            
        except Exception as e:
            logger.error(f"Error enviando resumen: {e}")

    def send_welcome_message(self):
        """Enviar mensaje de bienvenida al iniciar el sistema"""
        try:
            logger.info("📨 Enviando mensaje de bienvenida...")
            
            welcome_text = (
                "🚀 **¡Sistema de Monitoreo Iniciado!**\n\n"
                "🐕 Monitor de Emociones Caninas está activo\n"
                "📱 Usa /menu para acceder a todas las funciones\n\n"
                "El sistema comenzará a analizar a tu mascota automáticamente.\n"
                "Recibirás alertas si se detectan patrones preocupantes.\n\n"
                "⚠️ **IMPORTANTE**: Si no recibes alertas, revisa:\n"
                "• Que el monitoreo esté activado desde /menu\n"
                "• Que las notificaciones de Telegram estén habilitadas"
            )
            
            # Envío asíncrono manejado de forma síncrona
            import asyncio
            import threading
            
            # Variable para almacenar el resultado
            welcome_result = {'success': False, 'error': None, 'message_id': None}
            
            async def _send_welcome_async():
                """Función async interna para envío de bienvenida"""
                try:
                    result = await self.bot.send_message(
                        chat_id=self.chat_id,
                        text=welcome_text,
                        parse_mode='Markdown'
                    )
                    logger.info(f"✅ Mensaje de bienvenida enviado - ID: {result.message_id}")
                    welcome_result['success'] = True
                    welcome_result['message_id'] = result.message_id
                except Exception as e:
                    welcome_result['error'] = e
                    logger.error(f"❌ Error en envío async de bienvenida: {e}")
            
            def _run_welcome():
                """Ejecutar envío de bienvenida en nuevo event loop"""
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(_send_welcome_async())
                except Exception as e:
                    welcome_result['error'] = e
                    logger.error(f"❌ Error en loop de bienvenida: {e}")
                finally:
                    try:
                        loop.close()
                    except:
                        pass
            
            # Ejecutar en hilo separado
            welcome_thread = threading.Thread(target=_run_welcome)
            welcome_thread.start()
            welcome_thread.join(timeout=10)  # Timeout de 10 segundos
            
            if welcome_thread.is_alive():
                logger.error("❌ Timeout enviando bienvenida")
                return
            
            if not welcome_result['success'] and welcome_result['error']:
                raise welcome_result['error']
            
        except Exception as e:
            logger.error(f"❌ Error enviando mensaje de bienvenida: {e}")
            logger.error(f"❌ Tipo de error: {type(e).__name__}")
            logger.error(f"❌ Detalles: {str(e)}")

    def test_connection(self):
        """Probar conexión de Telegram"""
        try:
            logger.info("🧪 Iniciando test de conexión...")
            
            # Usar asyncio para manejar métodos asíncronos
            import asyncio
            import time
            import threading
            
            # Variable para almacenar el resultado
            test_result = {'success': False, 'error': None, 'message_id': None}
            
            async def _test_async():
                """Función async interna para el test"""
                try:
                    start_time = time.time()
                    
                    # Verificar bot de forma asíncrona
                    bot_info = await self.bot.get_me()
                    verification_time = time.time() - start_time
                    logger.info(f"🤖 Bot encontrado: {bot_info.username} ({bot_info.first_name}) - {verification_time:.2f}s")
                    
                    # Probar envío de mensaje
                    start_time = time.time()
                    test_message = "🧪 **Test de Conexión**\n\nSi recibes este mensaje, Telegram funciona correctamente."
                    
                    result = await self.bot.send_message(
                        chat_id=self.chat_id,
                        text=test_message,
                        parse_mode='Markdown'
                    )
                    
                    send_time = time.time() - start_time
                    logger.info(f"✅ Test de Telegram exitoso - Mensaje ID: {result.message_id} - {send_time:.2f}s")
                    
                    test_result['success'] = True
                    test_result['message_id'] = result.message_id
                    
                except Exception as e:
                    test_result['error'] = e
                    logger.error(f"❌ Error en test async: {e}")
            
            def _run_test():
                """Ejecutar test en nuevo event loop"""
                try:
                    # Crear un loop completamente nuevo para este hilo
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    # Ejecutar el test
                    loop.run_until_complete(_test_async())
                    
                except Exception as e:
                    test_result['error'] = e
                    logger.error(f"❌ Error en loop: {e}")
                finally:
                    try:
                        loop.close()
                    except:
                        pass
            
            # Ejecutar en hilo separado para evitar conflictos con otros loops
            test_thread = threading.Thread(target=_run_test)
            test_thread.start()
            test_thread.join(timeout=15)  # Timeout de 15 segundos
            
            if test_thread.is_alive():
                logger.error("❌ Test timeout - El test tardó más de 15 segundos")
                return False
            
            if test_result['success']:
                logger.info(f"✅ Test completado exitosamente - ID: {test_result['message_id']}")
                return True
            elif test_result['error']:
                raise test_result['error']
            else:
                logger.error("❌ Test falló sin error específico")
                return False
            
        except Exception as e:
            logger.error(f"❌ Test de Telegram falló: {e}")
            logger.error(f"❌ Tipo de error: {type(e).__name__}")
            logger.error(f"❌ Detalles: {str(e)}")
            
            # Información adicional para diagnóstico
            logger.error(f"🔍 Chat ID usado: {self.chat_id}")
            logger.error(f"🔍 Token (primeros 10 chars): {self.token[:10]}...")
            
            return False

    def send_periodic_update(self):
        """Enviar actualización periódica (cada 30 minutos)"""
        import time
        current_time = time.time()
        
        # Solo enviar si han pasado al menos 30 minutos desde la última actualización
        if current_time - self.last_status_time > 1800:  # 30 minutos
            if self.emotion_history and self.monitoring_active:
                self.send_status_update()
                self.last_status_time = current_time

    def send_video_summary(self, video_stats):
        """Envía un resumen completo del análisis de video"""
        try:
            logger.info(f"🔍 Iniciando envío de resumen. Stats recibidas: {video_stats}")
            
            # Validar que tenemos stats válidas
            if not video_stats or not isinstance(video_stats, dict):
                logger.error(f"❌ Stats inválidas: {video_stats}")
                self.send_simple_message_plain("❌ Error: No se pudieron generar estadísticas válidas del análisis.")
                return False
            
            # Extraer información de las estadísticas
            video_name = video_stats.get('video_name', 'Video analizado')
            total_detections = video_stats.get('total_emotions', 0)
            dominant_emotion = video_stats.get('dominant_emotion', 'No detectado')
            emotion_distribution = video_stats.get('emotion_distribution', {})
            confidence_avg = video_stats.get('confidence_avg', 0.0)
            frames_processed = video_stats.get('frames_processed', 0)
            dog_detection_rate = video_stats.get('dog_detection_rate', 0.0)
            processing_speed = video_stats.get('processing_speed', 0.0)
            output_file = video_stats.get('output_file', None)
            
            logger.info(f"📊 Datos extraídos - Video: {video_name}, Detecciones: {total_detections}, Emoción dominante: {dominant_emotion}")
            
            # Crear mensaje principal
            mensaje = f"""🎬 ANÁLISIS DE VIDEO COMPLETADO

📁 Video: {video_name}
🔍 Detecciones totales: {total_detections}

🎯 Emoción dominante: {dominant_emotion.upper()}

📊 Distribución:"""
            
            logger.info(f"📝 Mensaje base creado. Distribución emocional: {emotion_distribution}")
            
            # Agregar distribución con emojis y barras de progreso
            emotion_emojis = {
                'happy': '😊',
                'relaxed': '😌', 
                'sad': '😢',
                'angry': '😠'
            }
            
            total_emotions = sum(emotion_distribution.values()) if emotion_distribution else 1
            logger.info(f"🧮 Total emociones para cálculo: {total_emotions}")
            
            for emotion, count in emotion_distribution.items():
                if count > 0:
                    percentage = (count / total_emotions) * 100
                    emoji = emotion_emojis.get(emotion, '🐕')
                    
                    # Crear barra visual simple
                    bar_length = int(percentage / 10)  # Cada 10% = 1 cuadrado
                    bar = '█' * bar_length + '░' * (10 - bar_length)
                    
                    mensaje += f"\n{emoji} {emotion.upper()}: {count} ({percentage:.0f}%) {bar}"
                    logger.info(f"➕ Agregada emoción: {emotion} - {count} veces ({percentage:.0f}%)")
            
            # Agregar estadísticas técnicas
            mensaje += f"\n\n📈 Estadísticas:"
            mensaje += f"\n📊 Confianza promedio: {confidence_avg:.2f}"
            mensaje += f"\n⏱️ Frames procesados: {frames_processed}"
            mensaje += f"\n🐕 Detección de perros: {dog_detection_rate:.1f}%"
            mensaje += f"\n⚡ Velocidad: {processing_speed:.1f} FPS"
            
            logger.info("📈 Estadísticas técnicas agregadas al mensaje")
            
            # Agregar recomendaciones
            recommendations = {
                'happy': "¡Excelente! Tu perro muestra signos de felicidad. 🎉\n• Continúa con las actividades que lo hacen feliz\n• Es un buen momento para entrenamientos positivos",
                'relaxed': "Perfecto estado de relajación. 😌\n• Mantén el ambiente tranquilo\n• Tu perro está en su zona de confort",
                'sad': "Se detectó tristeza en tu mascota. 💙\n• Dedica más tiempo de calidad juntos\n• Verifica que no haya molestias físicas\n• Considera actividades estimulantes",
                'angry': "Signos de estrés o molestia detectados. ❤️\n• Identifica posibles fuentes de estrés\n• Proporciona un espacio tranquilo\n• Si persiste, consulta al veterinario"
            }
            
            recommendation = recommendations.get(dominant_emotion.lower(), "Continúa monitoreando el bienestar de tu mascota.")
            mensaje += f"\n\n💡 Recomendación:\n{recommendation}"
            
            logger.info(f"💡 Recomendación agregada para emoción: {dominant_emotion.lower()}")
            
            # Información del archivo guardado
            if output_file:
                mensaje += f"\n\n💾 Video procesado guardado:\n{os.path.basename(output_file)}"
                logger.info(f"💾 Info de archivo agregada: {os.path.basename(output_file)}")
            
            # Agregar timestamp
            from datetime import datetime
            timestamp = datetime.now().strftime("%d/%m/%Y %H:%M")
            mensaje += f"\n\n🕐 Análisis completado: {timestamp}"
            
            logger.info(f"📤 Enviando mensaje completo ({len(mensaje)} caracteres)")
            
            # Enviar mensaje sin Markdown para evitar errores de parsing
            success = self.send_simple_message_plain(mensaje)
            
            if success:
                logger.info("✅ Resumen de video enviado por Telegram exitosamente")
            else:
                logger.error("❌ Error al enviar resumen por Telegram")
                
            return success
            
        except Exception as e:
            logger.error(f"❌ Error enviando resumen de video: {e}")
            return False

    def send_simple_message_plain(self, text):
        """Enviar mensaje simple sin formato Markdown usando requests"""
        try:
            logger.info(f"📱 Enviando mensaje plain ({len(text)} caracteres): {text[:50]}...")
            
            url = f"https://api.telegram.org/bot{self.token}/sendMessage"
            data = {
                'chat_id': self.chat_id,
                'text': text
            }
            
            logger.info(f"🌐 URL: {url}")
            logger.info(f"📊 Chat ID: {self.chat_id}")
            
            response = requests.post(url, json=data, timeout=15)
            
            logger.info(f"📡 Response status: {response.status_code}")
            
            if response.status_code == 200:
                logger.info("✅ Mensaje plain enviado exitosamente")
                response_data = response.json()
                logger.info(f"📬 Message ID: {response_data.get('result', {}).get('message_id', 'N/A')}")
                return True
            else:
                logger.error(f"❌ Error HTTP enviando mensaje plain: {response.status_code}")
                logger.error(f"❌ Response text: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error enviando mensaje plain: {e}")
            logger.error(f"❌ Exception type: {type(e).__name__}")
            return False

    def send_simple_message(self, text):
        """Enviar mensaje simple de forma síncrona usando requests"""
        try:
            logger.info(f"📱 Enviando mensaje: {text[:50]}...")
            
            url = f"https://api.telegram.org/bot{self.token}/sendMessage"
            data = {
                'chat_id': self.chat_id,
                'text': text,
                'parse_mode': 'Markdown'
            }
            
            response = requests.post(url, json=data, timeout=15)
            
            if response.status_code == 200:
                logger.info("✅ Mensaje enviado exitosamente")
                return True
            else:
                logger.error(f"❌ Error HTTP enviando mensaje: {response.status_code} - {response.text}")
                # Si falla con Markdown, intentar sin formato
                logger.info("🔄 Reintentando sin formato Markdown...")
                data_plain = {
                    'chat_id': self.chat_id,
                    'text': text
                }
                response_plain = requests.post(url, json=data_plain, timeout=15)
                if response_plain.status_code == 200:
                    logger.info("✅ Mensaje enviado sin formato")
                    return True
                return False
                
        except Exception as e:
            logger.error(f"❌ Error enviando mensaje: {e}")
            return False

    async def _handle_video(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Manejar videos enviados por el usuario"""
        try:
            logger.info("📎 Video recibido desde Telegram")
            
            # Enviar mensaje de confirmación
            await update.message.reply_text(
                "🎬 **Video recibido**\n\n"
                "⏳ Descargando y procesando tu video...\n"
                "📊 Esto puede tomar algunos minutos dependiendo del tamaño.\n\n"
                "🐕 Estoy analizando las emociones de tu mascota...",
                parse_mode='Markdown'
            )
            
            video = update.message.video
            
            # Verificar tamaño del video (máximo 20MB)
            if video.file_size > 20 * 1024 * 1024:  # 20MB
                await update.message.reply_text(
                    "❌ **Video muy grande**\n\n"
                    "El video es demasiado grande (máximo 20MB).\n"
                    "Por favor, envía un video más corto o comprimido.",
                    parse_mode='Markdown'
                )
                return
            
            # Crear nombre de archivo único
            import time
            timestamp = int(time.time())
            video_filename = f"telegram_video_{timestamp}.mp4"
            video_path = os.path.join(os.getcwd(), video_filename)
            
            # Descargar el video
            file = await context.bot.get_file(video.file_id)
            await file.download_to_drive(video_path)
            
            logger.info(f"📥 Video descargado: {video_path}")
            
            # Enviar actualización de progreso
            await update.message.reply_text(
                "✅ **Video descargado**\n\n"
                "🧠 Iniciando análisis de IA...\n"
                "🔍 Detectando perros y analizando emociones...",
                parse_mode='Markdown'
            )
            
            # Procesar el video en un hilo separado para no bloquear
            import threading
            processing_thread = threading.Thread(
                target=self._process_video_thread,
                args=(video_path, update.message.chat_id, timestamp)
            )
            processing_thread.start()
            
        except Exception as e:
            logger.error(f"❌ Error manejando video: {e}")
            await update.message.reply_text(
                "❌ **Error procesando video**\n\n"
                "Hubo un problema al procesar tu video.\n"
                "Por favor, intenta nuevamente con un video diferente.",
                parse_mode='Markdown'
            )

    def _process_video_thread(self, video_path, chat_id, timestamp):
        """Procesar video en hilo separado"""
        try:
            # Importar las clases necesarias
            from .cam_utils import EmotionDetector
            from .yolo_dog_detector import YoloDogDetector
            import cv2
            
            logger.info("🧠 Cargando modelos de IA...")
            
            # Inicializar detectores
            detector = EmotionDetector("modelo/mejor_modelo_83.h5")
            yolo_detector = YoloDogDetector(confidence_threshold=0.60)
            
            # Nombre del archivo de salida
            output_filename = f"telegram_processed_{timestamp}.mp4"
            output_path = os.path.join(os.getcwd(), output_filename)
            
            logger.info(f"🎬 Procesando video: {video_path}")
            
            # Procesar el video usando la función existente
            success = self._process_video_for_telegram(
                video_path, output_path, detector, yolo_detector, chat_id
            )
            
            if success:
                # Enviar video procesado y resumen
                self._send_processed_video_results(output_path, chat_id, timestamp)
            else:
                # Enviar mensaje de error
                asyncio.run(self._send_error_message(chat_id))
            
        except Exception as e:
            logger.error(f"❌ Error en hilo de procesamiento: {e}")
            asyncio.run(self._send_error_message(chat_id))
        finally:
            # Limpiar archivos temporales
            try:
                if os.path.exists(video_path):
                    os.remove(video_path)
                    logger.info(f"🧹 Archivo temporal eliminado: {video_path}")
            except Exception as cleanup_error:
                logger.warning(f"⚠️ Error limpiando archivo temporal: {cleanup_error}")

    def _process_video_for_telegram(self, input_path, output_path, detector, yolo_detector, chat_id):
        """Procesar video específicamente para Telegram usando procesador limpio"""
        try:
            logger.info("🎬 Usando procesador de video optimizado...")
            
            # Importar y usar el procesador limpio
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(__file__)))
            
            from procesar_video import process_video
            
            # Procesar video con el sistema limpio
            stats = process_video(
                video_path=input_path,
                output_path=output_path,
                show_video=False,  # No mostrar ventana en modo Telegram
                save_video=True    # Siempre guardar para Telegram
            )
            
            if stats and stats.get('emotions_detected', 0) > 0:
                # Guardar estadísticas para el resumen
                self._current_video_stats = {
                    'video_name': stats.get('video_name', os.path.basename(input_path)),
                    'total_emotions': stats.get('emotions_detected', 0),
                    'emotion_distribution': stats.get('emotion_distribution', {}),
                    'dominant_emotion': stats.get('dominant_emotion', 'no_detected'),
                    'confidence_avg': stats.get('confidence_avg', 0.75),
                    'frames_processed': stats.get('total_frames', 0),
                    'dog_detection_rate': stats.get('dog_detection_rate', 0.0),
                    'processing_speed': stats.get('fps_processed', 0.0),
                    'output_file': stats.get('output_file', output_path)
                }
                
                logger.info(f"✅ Video procesado exitosamente: {output_path}")
                return True
            else:
                logger.warning("⚠️ No se detectaron emociones en el video")
                
                # Crear stats básicos para casos sin detección
                self._current_video_stats = {
                    'video_name': stats.get('video_name', os.path.basename(input_path)) if stats else os.path.basename(input_path),
                    'total_emotions': 0,
                    'emotion_distribution': {},
                    'dominant_emotion': 'no_detected',
                    'confidence_avg': 0.0,
                    'frames_processed': stats.get('total_frames', 0) if stats else 0,
                    'dog_detection_rate': 0.0,
                    'processing_speed': stats.get('fps_processed', 0.0) if stats else 0.0,
                    'output_file': output_path
                }
                return True
                
        except Exception as e:
            logger.error(f"❌ Error procesando video: {e}")
            return False

    async def _send_progress_update(self, chat_id, progress):
        """Enviar actualización de progreso"""
        try:
            if progress % 25 == 0:  # Solo enviar cada 25%
                await self.bot.send_message(
                    chat_id=chat_id,
                    text=f"⏳ **Progreso:** {progress:.0f}% completado",
                    parse_mode='Markdown'
                )
        except Exception as e:
            logger.error(f"Error enviando progreso: {e}")

    async def _send_error_message(self, chat_id):
        """Enviar mensaje de error"""
        try:
            await self.bot.send_message(
                chat_id=chat_id,
                text="❌ **Error procesando video**\n\n"
                     "Hubo un problema durante el análisis.\n"
                     "Por favor, intenta con otro video.",
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Error enviando mensaje de error: {e}")

    def _send_processed_video_results(self, output_path, chat_id, timestamp):
        """Enviar video procesado y resumen"""
        try:
            logger.info(f"📤 Enviando resultados al chat {chat_id}...")
            
            # **IMPORTANTE: Usar el chat_id del usuario, no el del bot**
            original_chat_id = self.chat_id  # Guardar el original
            self.chat_id = chat_id  # Cambiar temporalmente al chat del usuario
            
            # Enviar video procesado
            video_sent = self._send_video_file(chat_id, output_path)
            logger.info(f"📹 Video enviado: {'✅ Éxito' if video_sent else '❌ Error'}")
            
            # Verificar si tenemos estadísticas para el resumen
            if hasattr(self, '_current_video_stats'):
                logger.info(f"📊 Estadísticas encontradas: {self._current_video_stats}")
                logger.info("📝 Enviando resumen de video...")
                summary_sent = self.send_video_summary(self._current_video_stats)
                logger.info(f"📄 Resumen enviado: {'✅ Éxito' if summary_sent else '❌ Error'}")
            else:
                logger.error("❌ No se encontraron estadísticas del video (_current_video_stats)")
                # Enviar mensaje de error al usuario
                self.send_simple_message_plain("❌ Error: No se pudieron generar las estadísticas del análisis.")
            
            # Enviar mensaje final con opciones de navegación
            self._send_completion_message(chat_id)
            
            # **IMPORTANTE: Restaurar el chat_id original**
            self.chat_id = original_chat_id
            
        except Exception as e:
            logger.error(f"❌ Error enviando resultados: {e}")
            # Enviar mensaje de error al usuario usando el chat_id correcto
            original_chat_id = self.chat_id
            self.chat_id = chat_id
            self.send_simple_message_plain(f"❌ Error enviando resultados: {str(e)[:100]}...")
            self.chat_id = original_chat_id
        finally:
            # Limpiar archivo procesado
            try:
                if os.path.exists(output_path):
                    os.remove(output_path)
                    logger.info(f"🧹 Archivo procesado eliminado: {output_path}")
            except Exception as cleanup_error:
                logger.warning(f"⚠️ Error limpiando archivo procesado: {cleanup_error}")

    def _send_completion_message(self, chat_id):
        """Enviar mensaje de finalización con opciones de navegación"""
        try:
            import requests
            
            url = f"https://api.telegram.org/bot{self.token}/sendMessage"
            
            # Crear botones de navegación
            keyboard = {
                "inline_keyboard": [
                    [
                        {"text": "🎬 Analizar Otro Video", "callback_data": "video_analysis"},
                        {"text": "📹 Análisis en Tiempo Real", "callback_data": "realtime_analysis"}
                    ],
                    [
                        {"text": "📊 Ver Estado", "callback_data": "status"},
                        {"text": "🏠 Regresar al Menú", "callback_data": "show_menu"}
                    ]
                ]
            }
            
            data = {
                'chat_id': chat_id,
                'text': "✅ **ANÁLISIS COMPLETADO**\n\n🎉 Tu video ha sido procesado exitosamente\n📱 ¿Qué te gustaría hacer ahora?",
                'parse_mode': 'Markdown',
                'reply_markup': str(keyboard).replace("'", '"')
            }
            
            response = requests.post(url, json=data, timeout=15)
            if response.status_code == 200:
                logger.info("✅ Mensaje de finalización enviado")
            else:
                logger.error(f"❌ Error enviando mensaje de finalización: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Error enviando mensaje de finalización: {e}")

    def _send_video_file(self, chat_id, video_path):
        """Enviar archivo de video por Telegram usando requests"""
        try:
            # Verificar que el archivo existe y no está vacío
            if not os.path.exists(video_path) or os.path.getsize(video_path) == 0:
                logger.error(f"❌ Video no válido: {video_path}")
                self.send_simple_message_plain("❌ Error: El video procesado está vacío o no se generó correctamente.")
                return False
            
            # Enviar mensaje de que se está enviando
            self.send_simple_message_plain("📤 Enviando video analizado...\n\n🎬 Tu video con análisis de emociones está listo.")
            
            # Enviar el video usando requests
            logger.info(f"📹 Enviando video: {video_path}")
            
            url = f"https://api.telegram.org/bot{self.token}/sendVideo"
            
            with open(video_path, 'rb') as video_file:
                files = {'video': video_file}
                data = {
                    'chat_id': chat_id,
                    'caption': "🎬 Video Analizado\n\n✅ Análisis de emociones completado\n🐕 Detecciones YOLO superpuestas\n📊 Resumen detallado a continuación"
                }
                
                response = requests.post(url, files=files, data=data, timeout=300)  # 5 minutos timeout
                
                if response.status_code == 200:
                    logger.info("✅ Video enviado exitosamente por Telegram")
                    return True
                else:
                    logger.error(f"❌ Error HTTP enviando video: {response.status_code} - {response.text}")
                    self.send_simple_message_plain(f"❌ Error enviando video\n\nNo se pudo enviar el video procesado.\nCódigo de error: {response.status_code}")
                    return False
            
        except Exception as e:
            logger.error(f"❌ Error enviando video: {e}")
            self.send_simple_message_plain(f"❌ Error enviando video\n\nNo se pudo enviar el video procesado.\nError: {str(e)[:100]}...")
            return False

    def _get_emotion_distribution(self, emotion_history):
        """Calcular distribución de emociones"""
        distribution = {}
        for emotion in emotion_history:
            distribution[emotion] = distribution.get(emotion, 0) + 1
        return distribution

    def _get_dominant_emotion(self, emotion_history):
        """Obtener emoción dominante"""
        if not emotion_history:
            return "No detectado"
        
        distribution = self._get_emotion_distribution(emotion_history)
        return max(distribution.items(), key=lambda x: x[1])[0] if distribution else "No detectado"

    def clear_chat_sync(self):
        """Limpiar chat de forma síncrona"""
        try:
            import asyncio
            import threading
            
            # Variable para almacenar el resultado
            clear_result = {'success': False, 'error': None, 'deleted_count': 0}
            
            async def _clear_async():
                """Función async interna para limpieza"""
                try:
                    # Enviar mensaje temporal para obtener ID
                    temp_msg = await self.bot.send_message(
                        chat_id=self.chat_id,
                        text="🧹 Limpiando chat..."
                    )
                    
                    # Usar el ID del mensaje temporal para eliminar mensajes anteriores
                    deleted_count = 0
                    current_id = temp_msg.message_id
                    
                    # Intentar eliminar mensajes anteriores
                    for i in range(1, 21):
                        try:
                            message_id_to_delete = current_id - i
                            if message_id_to_delete > 0:
                                await self.bot.delete_message(
                                    chat_id=self.chat_id, 
                                    message_id=message_id_to_delete
                                )
                                deleted_count += 1
                        except Exception:
                            continue
                    
                    # Eliminar el mensaje temporal también
                    try:
                        await self.bot.delete_message(
                            chat_id=self.chat_id, 
                            message_id=current_id
                        )
                    except Exception:
                        pass
                    
                    # Enviar confirmación
                    await self.bot.send_message(
                        chat_id=self.chat_id,
                        text=f"✅ Chat limpiado: {deleted_count} mensajes eliminados"
                    )
                    
                    clear_result['success'] = True
                    clear_result['deleted_count'] = deleted_count
                    
                except Exception as e:
                    clear_result['error'] = e
                    logger.error(f"❌ Error en limpieza async: {e}")
            
            def _run_clear():
                """Ejecutar limpieza en nuevo event loop"""
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(_clear_async())
                except Exception as e:
                    clear_result['error'] = e
                    logger.error(f"❌ Error en loop de limpieza: {e}")
                finally:
                    try:
                        loop.close()
                    except:
                        pass
            
            # Ejecutar en hilo separado
            clear_thread = threading.Thread(target=_run_clear)
            clear_thread.start()
            clear_thread.join(timeout=15)  # Timeout de 15 segundos
            
            if clear_thread.is_alive():
                logger.error("❌ Timeout limpiando chat")
                return False
            
            if clear_result['success']:
                logger.info(f"🧹 {clear_result['deleted_count']} mensajes eliminados desde main.py")
                return True
            elif clear_result['error']:
                raise clear_result['error']
            else:
                return False
            
        except Exception as e:
            logger.error(f"❌ Error limpiando chat desde main.py: {e}")
            return False

    def _get_current_time(self):
        """Obtiene la hora actual formateada"""
        return datetime.now().strftime("%H:%M:%S")

    async def _clear_chat_messages(self, query):
        """Intentar limpiar mensajes del chat"""
        try:
            deleted_count = 0
            current_message_id = query.message.message_id
            
            # Intentar eliminar los últimos 20 mensajes
            for i in range(1, 21):
                try:
                    message_id_to_delete = current_message_id - i
                    if message_id_to_delete > 0:
                        await self.bot.delete_message(
                            chat_id=self.chat_id, 
                            message_id=message_id_to_delete
                        )
                        deleted_count += 1
                        # Pequeña pausa para evitar rate limiting
                        await asyncio.sleep(0.1)
                except Exception as msg_error:
                    # Continuar con el siguiente mensaje si este falla
                    continue
            
            logger.info(f"🧹 {deleted_count} mensajes eliminados del chat")
            
            if deleted_count == 0:
                raise Exception("No se pudieron eliminar mensajes")
            
        except Exception as e:
            logger.error(f"Error limpiando chat: {e}")
            raise

    def cleanup(self):
        """Limpiar recursos del bot de forma simple"""
        try:
            logger.info("🛑 Deteniendo bot de Telegram...")
            
            # Simplemente marcar como no ejecutándose y cerrar
            if self.application:
                try:
                    # Parar de forma simple sin asyncio
                    if hasattr(self.application, 'stop_running'):
                        self.application.stop_running()
                    else:
                        logger.info("ℹ️ Método stop_running no disponible, usando limpieza manual")
                except Exception as e:
                    # Error esperado en algunos casos, no es crítico
                    logger.debug(f"⚠️ Info en stop_running: {e}")
                
                # Marcar como None para evitar más operaciones
                self.application = None
            
            # Marcar bot thread como terminado
            if self.bot_thread and self.bot_thread.is_alive():
                try:
                    # Dar tiempo para que termine naturalmente
                    self.bot_thread.join(timeout=2)
                except Exception as e:
                    logger.warning(f"⚠️ Error esperando hilo: {e}")
            
            logger.info("✅ Bot de Telegram cerrado correctamente")
                
        except Exception as e:
            logger.error(f"❌ Error cerrando bot: {e}")
            # Si todo falla, al menos marcar como None
            self.application = None
