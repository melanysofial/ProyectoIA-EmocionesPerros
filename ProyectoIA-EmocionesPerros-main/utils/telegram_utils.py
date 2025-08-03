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
    def __init__(self, token, chat_id):
        self.token = token
        self.chat_id = chat_id
        self.application = None
        self.bot_thread = None
        self.monitoring_active = True  # Activado por defecto para alertas automáticas
        self.emotion_history = []
        self.last_status_time = 0
        
        # Cola thread-safe para alertas
        import queue
        self.alert_queue = queue.Queue()
        self.alert_processor_running = False
        
        # Crear bot con timeouts más agresivos
        try:
            logger.info("🔧 Creando bot con configuración optimizada...")
            self.bot = telegram.Bot(
                token=token,
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
        """Mostrar menú principal"""
        keyboard = [
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
        
        if query.data == "status":
            status_text = self._get_current_status()
            # Agregar botón de mostrar menú
            keyboard = [[InlineKeyboardButton("� Mostrar Menú", callback_data="show_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            # Enviar mensaje nuevo en lugar de editar
            await query.message.reply_text(status_text, reply_markup=reply_markup, parse_mode='Markdown')
            
        elif query.data == "summary":
            summary_text = self._get_daily_summary()
            keyboard = [[InlineKeyboardButton("� Mostrar Menú", callback_data="show_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            # Enviar mensaje nuevo en lugar de editar
            await query.message.reply_text(summary_text, reply_markup=reply_markup, parse_mode='Markdown')
            
        elif query.data == "monitor_on":
            self.monitoring_active = True
            keyboard = [[InlineKeyboardButton("� Mostrar Menú", callback_data="show_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            # Enviar mensaje nuevo en lugar de editar
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
            keyboard = [[InlineKeyboardButton("� Mostrar Menú", callback_data="show_menu")]]
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
            
        elif query.data == "show_menu" or query.data == "back_to_menu":
            # Mostrar menú como mensaje nuevo
            await self._menu_command(update, context)

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
            
            # Crear mensaje principal
            mensaje = f"""🎬 **ANÁLISIS DE VIDEO COMPLETADO**

📁 **Video:** {video_name}
🔍 **Detecciones totales:** {total_detections}

🎯 **Emoción dominante:** {dominant_emotion.upper()}

📊 **Distribución:**"""
            
            # Agregar distribución con emojis y barras de progreso
            emotion_emojis = {
                'happy': '😊',
                'relaxed': '😌', 
                'sad': '😢',
                'angry': '😠'
            }
            
            total_emotions = sum(emotion_distribution.values()) if emotion_distribution else 1
            
            for emotion, count in emotion_distribution.items():
                if count > 0:
                    percentage = (count / total_emotions) * 100
                    emoji = emotion_emojis.get(emotion, '🐕')
                    
                    # Crear barra visual simple
                    bar_length = int(percentage / 10)  # Cada 10% = 1 cuadrado
                    bar = '█' * bar_length + '░' * (10 - bar_length)
                    
                    mensaje += f"\n{emoji} **{emotion.upper()}:** {count} ({percentage:.0f}%) {bar}"
            
            # Agregar estadísticas técnicas
            mensaje += f"\n\n📈 **Estadísticas:**"
            mensaje += f"\n📊 Confianza promedio: {confidence_avg:.2f}"
            mensaje += f"\n⏱️ Frames procesados: {frames_processed}"
            mensaje += f"\n🐕 Detección de perros: {dog_detection_rate:.1f}%"
            mensaje += f"\n⚡ Velocidad: {processing_speed:.1f} FPS"
            
            # Agregar recomendaciones
            recommendations = {
                'happy': "¡Excelente! Tu perro muestra signos de felicidad. 🎉\n• Continúa con las actividades que lo hacen feliz\n• Es un buen momento para entrenamientos positivos",
                'relaxed': "Perfecto estado de relajación. 😌\n• Mantén el ambiente tranquilo\n• Tu perro está en su zona de confort",
                'sad': "Se detectó tristeza en tu mascota. 💙\n• Dedica más tiempo de calidad juntos\n• Verifica que no haya molestias físicas\n• Considera actividades estimulantes",
                'angry': "Signos de estrés o molestia detectados. ❤️\n• Identifica posibles fuentes de estrés\n• Proporciona un espacio tranquilo\n• Si persiste, consulta al veterinario"
            }
            
            recommendation = recommendations.get(dominant_emotion.lower(), "Continúa monitoreando el bienestar de tu mascota.")
            mensaje += f"\n\n💡 **Recomendación:**\n{recommendation}"
            
            # Información del archivo guardado
            if output_file:
                mensaje += f"\n\n💾 **Video procesado guardado:**\n`{output_file}`"
            
            # Agregar timestamp
            from datetime import datetime
            timestamp = datetime.now().strftime("%d/%m/%Y %H:%M")
            mensaje += f"\n\n🕐 Análisis completado: {timestamp}"
            
            # Enviar mensaje
            self.send_simple_message(mensaje)
            logger.info("📱 Resumen de video enviado por Telegram")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error enviando resumen de video: {e}")
            return False

    def send_simple_message(self, text):
        """Enviar mensaje simple de forma síncrona"""
        try:
            import asyncio
            import threading
            
            # Variable para almacenar el resultado
            send_result = {'success': False, 'error': None}
            
            async def _send_async():
                """Función async interna para envío"""
                try:
                    await self.bot.send_message(
                        chat_id=self.chat_id,
                        text=text,
                        parse_mode='Markdown'
                    )
                    logger.info(f"📱 Mensaje simple enviado: {text[:50]}...")
                    send_result['success'] = True
                except Exception as e:
                    send_result['error'] = e
                    logger.error(f"❌ Error en envío async: {e}")
            
            def _run_send():
                """Ejecutar envío en nuevo event loop"""
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(_send_async())
                except Exception as e:
                    send_result['error'] = e
                    logger.error(f"❌ Error en loop de envío: {e}")
                finally:
                    try:
                        loop.close()
                    except:
                        pass
            
            # Ejecutar en hilo separado
            send_thread = threading.Thread(target=_run_send)
            send_thread.start()
            send_thread.join(timeout=10)  # Timeout de 10 segundos
            
            if send_thread.is_alive():
                logger.error("❌ Timeout enviando mensaje simple")
                return False
            
            if send_result['success']:
                return True
            elif send_result['error']:
                raise send_result['error']
            else:
                return False
                
        except Exception as e:
            logger.error(f"❌ Error enviando mensaje simple: {e}")
            return False

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
        """Limpiar recursos del bot"""
        try:
            if self.application:
                logger.info("🛑 Deteniendo bot de Telegram...")
                # Forzar parada más agresiva
                if self.application.running:
                    self.application.stop_running()
                
                # Usar método más directo para cerrar
                try:
                    import asyncio
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(self.application.shutdown())
                    loop.close()
                except Exception as shutdown_error:
                    logger.warning(f"Error en shutdown normal: {shutdown_error}")
                    # Método más agresivo
                    try:
                        self.application.updater.stop()
                    except:
                        pass
                
                self.application = None
                logger.info("✅ Bot de Telegram cerrado correctamente")
            else:
                logger.info("ℹ️ Bot ya estaba cerrado")
                
        except Exception as e:
            logger.error(f"❌ Error cerrando bot: {e}")
            # Si todo falla, al menos marcar como None
            self.application = None
