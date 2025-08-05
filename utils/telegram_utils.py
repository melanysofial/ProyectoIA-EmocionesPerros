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
import random
import string
import socket
import tkinter as tk
from tkinter import messagebox, ttk
import webbrowser

logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self, token=None, chat_id=None):
        # Obtener token y chat_id de parámetros o variables de entorno
        self.token = token or os.getenv('TELEGRAM_BOT_TOKEN', '7668982184:AAEXrM7xx0bDKidNOhyi6xjSNYUNRpvu61U')
        self.chat_id = chat_id or os.getenv('TELEGRAM_CHAT_ID', '1673887715')
        
        if not self.token:
            raise ValueError("❌ Token de Telegram no proporcionado. Usa el parámetro 'token' o la variable de entorno 'TELEGRAM_BOT_TOKEN'")
        
        # Sistema de códigos de vinculación por PC
        self.pc_name = socket.gethostname()  # Nombre de la PC - DEBE IR PRIMERO
        self.connection_code = self._generate_connection_code()
        self.authorized_users = set()  # Set de chat_ids autorizados
        
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
        self.current_frame = None     # Frame actual para captura remota
        self.frame_lock = threading.Lock()  # Lock para acceso thread-safe al frame
        
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
        
        # Mostrar código de conexión al iniciar
        self._show_connection_code()

    def _generate_connection_code(self):
        """Generar código único de conexión para esta PC"""
        # Combinar nombre de PC + timestamp + aleatorio para unicidad
        timestamp = str(int(time.time()))[-4:]  # Últimos 4 dígitos del timestamp
        random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        pc_part = self.pc_name[:4].upper() if len(self.pc_name) >= 4 else self.pc_name.upper().ljust(4, 'X')
        
        code = f"{pc_part}-{timestamp}-{random_part}"
        return code
    
    def _show_connection_code(self):
        """Mostrar código de conexión en ventana emergente amigable"""
        try:
            # Crear ventana emergente
            root = tk.Tk()
            root.title("🔐 FeeliPetAI - Código de Conexión")
            root.geometry("500x600")
            root.resizable(False, False)
            
            # Configurar icono y estilo
            root.configure(bg='#f0f0f0')
            
            # Centrar ventana en la pantalla
            root.update_idletasks()
            x = (root.winfo_screenwidth() // 2) - (500 // 2)
            y = (root.winfo_screenheight() // 2) - (600 // 2)
            root.geometry(f"500x600+{x}+{y}")
            
            # Frame principal con padding
            main_frame = tk.Frame(root, bg='#f0f0f0', padx=20, pady=20)
            main_frame.pack(fill=tk.BOTH, expand=True)
            
            # Título principal
            title_label = tk.Label(
                main_frame, 
                text="🔐 CÓDIGO DE CONEXIÓN TELEGRAM",
                font=("Arial", 16, "bold"),
                bg='#f0f0f0',
                fg='#2c3e50'
            )
            title_label.pack(pady=(0, 10))
            
            # Información de PC
            pc_frame = tk.Frame(main_frame, bg='#e8f4f8', relief=tk.RAISED, bd=2)
            pc_frame.pack(fill=tk.X, pady=(0, 15))
            
            pc_label = tk.Label(
                pc_frame,
                text=f"🖥️ PC: {self.pc_name}",
                font=("Arial", 12, "bold"),
                bg='#e8f4f8',
                fg='#34495e'
            )
            pc_label.pack(pady=10)
            
            # Frame para el código (destacado)
            code_frame = tk.Frame(main_frame, bg='#fff3cd', relief=tk.RAISED, bd=3)
            code_frame.pack(fill=tk.X, pady=(0, 20))
            
            code_title = tk.Label(
                code_frame,
                text="🔑 TU CÓDIGO DE CONEXIÓN:",
                font=("Arial", 11, "bold"),
                bg='#fff3cd',
                fg='#856404'
            )
            code_title.pack(pady=10)
            
            # Código en grande y seleccionable
            code_var = tk.StringVar(value=self.connection_code)
            code_entry = tk.Entry(
                code_frame,
                textvariable=code_var,
                font=("Courier New", 18, "bold"),
                justify=tk.CENTER,
                state='readonly',
                bg='#ffffff',
                fg='#d63384',
                relief=tk.SOLID,
                bd=2,
                width=20
            )
            code_entry.pack(pady=10)
            
            # Función para copiar código
            def copy_code():
                root.clipboard_clear()
                root.clipboard_append(self.connection_code)
                copy_btn.configure(text="✅ ¡Copiado!", bg='#28a745')
                root.after(2000, lambda: copy_btn.configure(text="📋 Copiar Código", bg='#007bff'))
            
            # Botón copiar
            copy_btn = tk.Button(
                code_frame,
                text="📋 Copiar Código",
                font=("Arial", 10, "bold"),
                bg='#007bff',
                fg='white',
                padx=20,
                pady=5,
                command=copy_code,
                relief=tk.RAISED,
                bd=2
            )
            copy_btn.pack(pady=10)
            
            # Instrucciones paso a paso
            instructions_frame = tk.Frame(main_frame, bg='#f8f9fa', relief=tk.RAISED, bd=2)
            instructions_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
            
            instructions_title = tk.Label(
                instructions_frame,
                text="📋 INSTRUCCIONES:",
                font=("Arial", 12, "bold"),
                bg='#f8f9fa',
                fg='#495057'
            )
            instructions_title.pack(pady=10)
            
            instructions = [
                "1️⃣ Abre Telegram en tu teléfono",
                "2️⃣ Busca el bot y envía /start",
                "3️⃣ Copia y envía el código: " + self.connection_code,
                "4️⃣ ¡Listo! Ya puedes controlar esta PC desde Telegram"
            ]
            
            for instruction in instructions:
                instr_label = tk.Label(
                    instructions_frame,
                    text=instruction,
                    font=("Arial", 10),
                    bg='#f8f9fa',
                    fg='#6c757d',
                    anchor='w'
                )
                instr_label.pack(fill=tk.X, padx=20, pady=2)
            
            # Separador
            separator = tk.Frame(main_frame, height=2, bg='#dee2e6')
            separator.pack(fill=tk.X, pady=10)
            
            # Información adicional
            info_label = tk.Label(
                main_frame,
                text="💡 Este código es único para esta PC\n🔒 Solo compártelo con personas de confianza\n⚠️ Cada PC tiene su código único - Este permite que CUALQUIER PERSONA controle esta PC desde Telegram",
                font=("Arial", 9),
                bg='#f0f0f0',
                fg='#6c757d',
                justify=tk.CENTER
            )
            info_label.pack(pady=10)
            
            # Botones de acción
            button_frame = tk.Frame(main_frame, bg='#f0f0f0')
            button_frame.pack(fill=tk.X)
            
            def close_window():
                root.destroy()
            
            def open_telegram():
                try:
                    webbrowser.open("https://telegram.org/")
                except:
                    pass
            
            # Botón cerrar
            close_btn = tk.Button(
                button_frame,
                text="✅ Entendido",
                font=("Arial", 11, "bold"),
                bg='#28a745',
                fg='white',
                padx=30,
                pady=8,
                command=close_window,
                relief=tk.RAISED,
                bd=2
            )
            close_btn.pack(side=tk.RIGHT)
            
            # Botón abrir Telegram
            telegram_btn = tk.Button(
                button_frame,
                text="📱 Abrir Telegram Web",
                font=("Arial", 10),
                bg='#0088cc',
                fg='white',
                padx=20,
                pady=8,
                command=open_telegram,
                relief=tk.RAISED,
                bd=2
            )
            telegram_btn.pack(side=tk.LEFT)
            
            # Seleccionar código automáticamente para fácil copia
            code_entry.select_range(0, tk.END)
            code_entry.focus()
            
            # Manejar cierre con X
            root.protocol("WM_DELETE_WINDOW", close_window)
            
            # Mostrar ventana
            root.mainloop()
            
        except Exception as e:
            logger.error(f"Error mostrando ventana de código: {e}")
            # Fallback a consola si falla la ventana
            self._show_connection_code_console()
    
    def _show_connection_code_console(self):
        """Mostrar código de conexión en consola (fallback)"""
        # Colores ANSI para terminal
        GREEN = '\033[92m'
        YELLOW = '\033[93m'
        RED = '\033[91m'
        CYAN = '\033[96m'
        MAGENTA = '\033[95m'
        BOLD = '\033[1m'
        UNDERLINE = '\033[4m'
        RESET = '\033[0m'
        
        # Borde decorativo
        border = "█" * 70
        inner_border = "▓" * 68
        
        print(f"\n{RED}{border}{RESET}")
        print(f"{RED}█{RESET}{YELLOW}{'':^68}{RESET}{RED}█{RESET}")
        print(f"{RED}█{RESET}{YELLOW}{BOLD}{'🔐 CÓDIGO DE CONEXIÓN PARA TELEGRAM':^68}{RESET}{RED}█{RESET}")
        print(f"{RED}█{RESET}{YELLOW}{'':^68}{RESET}{RED}█{RESET}")
        print(f"{RED}█{RESET}{CYAN}{inner_border}{RESET}{RED}█{RESET}")
        print(f"{RED}█{RESET}{GREEN}{'':^68}{RESET}{RED}█{RESET}")
        print(f"{RED}█{RESET}{GREEN}{BOLD}{'📱 PC: ' + self.pc_name:^68}{RESET}{RED}█{RESET}")
        print(f"{RED}█{RESET}{GREEN}{'':^68}{RESET}{RED}█{RESET}")
        print(f"{RED}█{RESET}{MAGENTA}{'▓' * 68}{RESET}{RED}█{RESET}")
        print(f"{RED}█{RESET}{MAGENTA}{'':^68}{RESET}{RED}█{RESET}")
        print(f"{RED}█{RESET}{MAGENTA}{BOLD}{UNDERLINE}{'🔑 CÓDIGO: ' + self.connection_code:^68}{RESET}{RED}█{RESET}")
        print(f"{RED}█{RESET}{MAGENTA}{'':^68}{RESET}{RED}█{RESET}")
        print(f"{RED}█{RESET}{MAGENTA}{'▓' * 68}{RESET}{RED}█{RESET}")
        print(f"{RED}█{RESET}{CYAN}{'':^68}{RESET}{RED}█{RESET}")
        print(f"{RED}█{RESET}{CYAN}{BOLD}{'📋 INSTRUCCIONES:':^68}{RESET}{RED}█{RESET}")
        print(f"{RED}█{RESET}{CYAN}{'1. Abre Telegram en tu teléfono':^68}{RESET}{RED}█{RESET}")
        print(f"{RED}█{RESET}{CYAN}{'2. Busca el bot y envía /start':^68}{RESET}{RED}█{RESET}")
        print(f"{RED}█{RESET}{CYAN}{BOLD}{'3. Envía el código: ' + self.connection_code:^68}{RESET}{RED}█{RESET}")
        print(f"{RED}█{RESET}{CYAN}{'4. ¡Listo! Ya puedes controlar esta PC desde Telegram':^68}{RESET}{RED}█{RESET}")
        print(f"{RED}█{RESET}{YELLOW}{'':^68}{RESET}{RED}█{RESET}")
        print(f"{RED}{border}{RESET}")
        
        # Código en formato grande para fácil lectura
        print(f"\n{YELLOW}{'🔥 CÓDIGO PARA COPIAR 🔥':^70}{RESET}")
        print(f"{GREEN}{'╔' + '═' * 68 + '╗'}{RESET}")
        print(f"{GREEN}║{RESET}{BOLD}{UNDERLINE}{self.connection_code:^68}{RESET}{GREEN}║{RESET}")
        print(f"{GREEN}{'╚' + '═' * 68 + '╝'}{RESET}\n")
    
    def _is_user_authorized(self, chat_id):
        """Verificar si el usuario está autorizado para usar este bot"""
        return chat_id in self.authorized_users
    
    def _authorize_user(self, chat_id):
        """Autorizar un usuario para usar este bot"""
        self.authorized_users.add(chat_id)
        logger.info(f"✅ Usuario {chat_id} autorizado para PC {self.pc_name}")
    
    async def _handle_connection_code(self, message_text, chat_id):
        """Manejar códigos de conexión enviados por usuarios"""
        if message_text.strip().upper() == self.connection_code:
            self._authorize_user(chat_id)
            return True
        return False

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
            
            # Handler para mensajes de texto (códigos de conexión)
            self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_text_message))
            
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
        """Comando /start con sistema de autorización"""
        chat_id = update.message.chat_id
        user_name = update.message.from_user.first_name or "Usuario"
        
        if self._is_user_authorized(chat_id):
            # Usuario ya autorizado
            welcome_text = (
                f"🐕 **¡Bienvenido de vuelta, {user_name}!**\n\n"
                f"🖥️ **PC Conectada:** {self.pc_name}\n"
                f"🔑 **Estado:** Autorizado ✅\n\n"
                "Tu asistente personal para el bienestar de tu mascota está listo.\n\n"
                "Usa /menu para ver todas las opciones disponibles."
            )
            await update.message.reply_text(welcome_text, parse_mode='Markdown')
            await self._menu_command(update, context)
        else:
            # Usuario no autorizado - solicitar código
            welcome_text = (
                f"👋 **¡Hola {user_name}!**\n\n"
                "🐕 **Bienvenido a FeeliPetAI**\n"
                "🔐 **Sistema de Acceso Seguro Activado**\n\n"
                f"🖥️ **PC:** {self.pc_name}\n"
                f"🔑 **Estado:** Pendiente de autorización\n\n"
                "📋 **¿Cómo obtener acceso?**\n"
                "1️⃣ Ve a la PC donde está ejecutándose el servicio\n"
                "2️⃣ Busca el código colorido que aparece en pantalla\n"
                "3️⃣ Cópialo y envíalo aquí como mensaje\n\n"
                "🔑 **Formato del código:** XXXX-1234-ABCD\n\n"
                "💡 **Ejemplo:**\n"
                "Si ves `GAMI-5678-MNOP` en pantalla, envía:\n"
                "`GAMI-5678-MNOP`\n\n"
                "⚠️ **Nota:** Cada PC tiene su código único.\n"
                "🔒 **Seguridad:** Solo comparte códigos con personas de confianza."
            )
            await update.message.reply_text(welcome_text, parse_mode='Markdown')

    async def _handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Manejar mensajes de texto (principalmente códigos de conexión)"""
        chat_id = update.message.chat_id
        message_text = update.message.text
        user_name = update.message.from_user.first_name or "Usuario"
        
        # Si ya está autorizado, ignorar mensajes de texto
        if self._is_user_authorized(chat_id):
            await update.message.reply_text(
                "ℹ️ **Ya estás conectado**\n\n"
                "Usa /menu para acceder a las funciones del bot.",
                parse_mode='Markdown'
            )
            return
        
        # Intentar autorizar con el código
        if await self._handle_connection_code(message_text, chat_id):
            # Código correcto - autorizar usuario
            success_text = (
                f"🎉 **¡Conexión exitosa, {user_name}!**\n\n"
                f"✅ **Autorizado para PC:** {self.pc_name}\n"
                f"🔑 **Código utilizado:** {self.connection_code}\n\n"
                "🐕 **FeeliPetAI** está ahora disponible.\n\n"
                "Usa /menu para comenzar a monitorear a tu mascota."
            )
            await update.message.reply_text(success_text, parse_mode='Markdown')
            await self._menu_command(update, context)
        else:
            # Código incorrecto
            error_text = (
                "❌ **Código Incorrecto**\n\n"
                f"🔍 **Código recibido:** `{message_text}`\n"
                f"🖥️ **PC esperada:** {self.pc_name}\n\n"
                "💡 **Posibles problemas:**\n"
                "• ❗ Código copiado incorrectamente\n"
                "• ❗ Espacios o caracteres extra\n"
                "• ❗ Código de otra PC diferente\n"
                "• ❗ Aplicación reiniciada (código cambiado)\n\n"
                "🔄 **¿Qué hacer?**\n"
                "1️⃣ Ve a la PC y verifica el código actual\n"
                "2️⃣ Cópialo exactamente como aparece\n"
                "3️⃣ Envíalo sin espacios extra\n\n"
                "📋 **Formato:** XXXX-1234-ABCD\n"
                "🆘 **¿Necesitas ayuda?** Usa /start para ver instrucciones."
            )
            await update.message.reply_text(error_text, parse_mode='Markdown')

    async def _menu_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Mostrar menú principal con nuevas opciones"""
        # Verificar autorización
        chat_id = update.message.chat_id if update.message else update.callback_query.message.chat_id
        
        if not self._is_user_authorized(chat_id):
            unauthorized_text = (
                "🔐 **ACCESO DENEGADO**\n\n"
                "❌ No estás autorizado para usar este bot.\n\n"
                "📋 Para conectarte, envía el código de tu PC.\n"
                "Usa /start para ver las instrucciones."
            )
            
            if update.message:
                await update.message.reply_text(unauthorized_text, parse_mode='Markdown')
            else:
                await update.callback_query.message.reply_text(unauthorized_text, parse_mode='Markdown')
            return
        
        keyboard = [
            [InlineKeyboardButton("📹 Análisis en Tiempo Real", callback_data="realtime_analysis")],
            [InlineKeyboardButton("🎬 Analizar Video", callback_data="video_analysis")],
            [InlineKeyboardButton("📊 Estado Actual", callback_data="status")],
            [InlineKeyboardButton("📈 Resumen del Día", callback_data="summary")],
            [InlineKeyboardButton("🔔 Activar Monitoreo", callback_data="monitor_on")],
            [InlineKeyboardButton("🔕 Pausar Monitoreo", callback_data="monitor_off")],
            [InlineKeyboardButton("💡 Consejos Generales", callback_data="tips")],
            [InlineKeyboardButton("💎 Versión Premium", callback_data="premium_info")],
            [InlineKeyboardButton("🚪 Desconectar de PC", callback_data="disconnect_pc")],
            [InlineKeyboardButton("❓ Ayuda", callback_data="help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        menu_text = (
            "🎛️ **MENÚ PRINCIPAL**\n\n"
            f"🖥️ **PC:** {self.pc_name}\n"
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
        """Manejar clics en botones con manejo de errores mejorado"""
        query = update.callback_query
        
        # Verificar autorización primero
        chat_id = query.message.chat_id
        if not self._is_user_authorized(chat_id):
            try:
                await query.answer("❌ No autorizado", show_alert=True)
            except:
                pass  # Ignorar errores de query expirado
            
            await query.message.reply_text(
                "🔐 **ACCESO DENEGADO**\n\nUsa /start para autorizar tu acceso.",
                parse_mode='Markdown'
            )
            return
        
        # Intentar responder al callback query de forma segura
        try:
            await query.answer()
        except Exception as callback_error:
            # Ignorar errores de callback expirado
            logger.debug(f"Callback query expirado/inválido: {callback_error}")
            pass
        
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
            
        elif query.data == "disconnect_pc":
            # Confirmar antes de desconectar
            keyboard = [
                [InlineKeyboardButton("✅ Sí, desconectar", callback_data="confirm_disconnect")],
                [InlineKeyboardButton("❌ Cancelar", callback_data="show_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            # Enviar mensaje nuevo en lugar de editar
            await query.message.reply_text(
                "🚪 **Desconectar de PC**\n\n"
                f"🖥️ **PC actual:** {self.pc_name}\n\n"
                "⚠️ Esta acción te desconectará de esta PC.\n"
                "Tendrás que volver a ingresar el código para reconectarte.\n\n"
                "¿Estás seguro de que quieres desconectar?",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
        elif query.data == "confirm_disconnect":
            try:
                # Desautorizar al usuario
                chat_id = query.message.chat_id
                if chat_id in self.authorized_users:
                    self.authorized_users.remove(chat_id)
                
                # Mensaje de confirmación de desconexión
                await query.message.reply_text(
                    "✅ **Desconectado Exitosamente**\n\n"
                    f"🖥️ Has sido desconectado de **{self.pc_name}**\n\n"
                    "🔐 **Para reconectarte:**\n"
                    "1️⃣ Envía `/start`\n"
                    "2️⃣ Ingresa el código de conexión actual\n\n"
                    "👋 ¡Gracias por usar FeeliPetAI!",
                    parse_mode='Markdown'
                )
                
            except Exception as e:
                logger.error(f"Error desconectando usuario: {e}")
                await query.message.reply_text(
                    "❌ **Error al desconectar**\n\n"
                    "Hubo un problema al procesar la desconexión.\n"
                    "Usa /start para intentar reconectarte.",
                    parse_mode='Markdown'
                )
                
                await query.message.reply_text(
                    "🧹 **LIMPIEZA COMPLETADA**\n\n"
                    "✅ Se intentó limpiar los mensajes del bot\n"
                    "💡 Algunos mensajes pueden no eliminarse debido a limitaciones de Telegram\n"
                    "📊 El historial de análisis se mantiene intacto\n\n"
                    "Puedes eliminar mensajes manualmente si es necesario.",
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
                
            except Exception as e:
                logger.error(f"Error en limpieza de chat: {e}")
                
                # Enviar mensaje de error pero mantener conexión
                keyboard = [[InlineKeyboardButton("🏠 Regresar al Menú", callback_data="show_menu")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.message.reply_text(
                    "⚠️ **LIMPIEZA PARCIAL**\n\n"
                    "❌ Hubo problemas eliminando algunos mensajes\n"
                    "💡 Esto es normal debido a limitaciones de Telegram\n"
                    "🔧 Puedes intentar eliminar mensajes manualmente\n\n"
                    "El sistema continúa funcionando normalmente.",
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
            
        # Callback para confirmar pausa de análisis en tiempo real
        elif query.data == "confirm_pause_realtime":
            # Pausar análisis en tiempo real y proceder con análisis de video
            if self.realtime_active:
                await self._pause_realtime_analysis()
                await query.message.reply_text(
                    "⏸️ **Análisis en Tiempo Real Pausado**\n\n"
                    "✅ Análisis pausado exitosamente\n"
                    "🎬 Ahora puedes enviar videos para análisis\n\n"
                    "💡 Usa el botón 'Tiempo Real' cuando quieras reanudar.",
                    parse_mode='Markdown'
                )
            
            # Proceder con la solicitud de análisis de video
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
            
        elif query.data == "capture_frame":
            await self._capture_current_frame(update, context)
            
        elif query.data == "premium_info":
            premium_text = (
                "💎 **VERSIÓN PREMIUM**\n\n"
                "**🆓 PLAN BÁSICO (Actual):**\n"
                "• ✅ Análisis de hasta 5 videos por día\n"
                "• ✅ Consejos generales para perros\n"
                "• ✅ Detección básica de emociones\n"
                "• ❌ Sin análisis en tiempo real\n"
                "• ❌ Sin alertas automáticas\n"
                "• ❌ Sin reportes detallados\n"
                "• ❌ Sin resúmenes diarios\n\n"
                "**💎 PLAN PREMIUM ($3.00 USD):**\n"
                "• ✅ Análisis ilimitado de videos\n"
                "• ✅ Análisis en tiempo real por cámara\n"
                "• ✅ Alertas automáticas inteligentes\n"
                "• ✅ Reportes detallados y estadísticas\n"
                "• ✅ Resúmenes diarios personalizados\n"
                "• ✅ Consejos especializados por raza\n"
                "• ✅ Historial completo de análisis\n"
                "• ✅ Soporte prioritario\n\n"
                "**🎯 BENEFICIOS PREMIUM:**\n"
                "• Monitoreo 24/7 de tu mascota\n"
                "• Detección temprana de problemas\n"
                "• Análisis de patrones de comportamiento\n"
                "• Recomendaciones veterinarias\n\n"
                "💳 **Próximamente:** Sistema de pago integrado\n"
                "📧 **Contacto:** Escríbenos para más información\n\n"
                "¡Invierte $3 en el bienestar de tu mejor amigo! 🐕💖"
            )
            keyboard = [
                [InlineKeyboardButton("📊 Ver mis límites actuales", callback_data="usage_stats")],
                [InlineKeyboardButton("💳 Información de pago", callback_data="payment_info")],
                [InlineKeyboardButton("🏠 Regresar al Menú", callback_data="show_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.reply_text(premium_text, reply_markup=reply_markup, parse_mode='Markdown')
            
        elif query.data == "usage_stats":
            # Aquí implementaremos el contador de videos analizados
            stats_text = (
                "📊 **ESTADÍSTICAS DE USO**\n\n"
                "**📅 Hoy:**\n"
                "• Videos analizados: 0/5 📹\n"
                "• Plan actual: 🆓 Básico\n\n"
                "**📈 Esta semana:**\n"
                "• Total de análisis: 0\n"
                "• Días activos: 0/7\n\n"
                "**💡 Recomendación:**\n"
                "Con el plan Premium tendrías análisis ilimitados\n"
                "y funciones avanzadas como monitoreo en tiempo real.\n\n"
                "¡Actualiza por solo $1 y desbloquea todo el potencial! 💎"
            )
            keyboard = [
                [InlineKeyboardButton("💎 Ver Plan Premium", callback_data="premium_info")],
                [InlineKeyboardButton("🏠 Regresar al Menú", callback_data="show_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.reply_text(stats_text, reply_markup=reply_markup, parse_mode='Markdown')
            
        elif query.data == "payment_info":
            payment_text = (
                "💳 **INFORMACIÓN DE PAGO**\n\n"
                "**💎 Plan Premium - $1.00 USD**\n\n"
                "**🚧 PRÓXIMAMENTE:**\n"
                "• Integración con PayPal\n"
                "• Pago con tarjeta de crédito/débito\n"
                "• Activación automática instantánea\n\n"
                "**📧 POR AHORA:**\n"
                "Si estás interesado en el plan Premium,\n"
                "contáctanos y te daremos acceso anticipado:\n\n"
                "• Email: [Agregar email de contacto]\n"
                "• Telegram: [Agregar usuario admin]\n\n"
                "**🎁 OFERTA ESPECIAL:**\n"
                "Los primeros 100 usuarios obtendrán\n"
                "1 mes gratis adicional! 🎉\n\n"
                "¡No te pierdas esta oportunidad!"
            )
            keyboard = [
                [InlineKeyboardButton("💎 Ver Beneficios Premium", callback_data="premium_info")],
                [InlineKeyboardButton("🏠 Regresar al Menú", callback_data="show_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.reply_text(payment_text, reply_markup=reply_markup, parse_mode='Markdown')

    async def _handle_realtime_analysis(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Manejar el análisis en tiempo real"""
        query = update.callback_query
        
        if self.realtime_active:
            # Si ya está activo, mostrar opciones de control
            keyboard = [
                [InlineKeyboardButton("⏸️ Pausar Análisis", callback_data="pause_realtime")],
                [InlineKeyboardButton("📸 Ver Ahora", callback_data="capture_frame")],
                [InlineKeyboardButton("⏹️ Detener Análisis", callback_data="stop_realtime")],
                [InlineKeyboardButton("🎬 Cambiar a Video", callback_data="switch_to_video")],
                [InlineKeyboardButton("🏠 Regresar al Menú", callback_data="show_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.message.reply_text(
                "📹 **ANÁLISIS EN TIEMPO REAL ACTIVO**\n\n"
                "✅ El sistema está analizando a tu mascota en vivo\n"
                "📊 Recibes actualizaciones en tiempo real\n"
                "🔔 Alertas automáticas activadas\n"
                "📸 Puedes capturar frames instantáneos\n\n"
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
        
        # Verificar si hay análisis en tiempo real activo
        if self.realtime_active:
            # Mostrar advertencia antes de pausar
            keyboard = [
                [InlineKeyboardButton("✅ Sí, pausar y analizar video", callback_data="confirm_pause_realtime")],
                [InlineKeyboardButton("❌ No, mantener tiempo real", callback_data="realtime_analysis")],
                [InlineKeyboardButton("🏠 Regresar al Menú", callback_data="show_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.message.reply_text(
                "⚠️ **ANÁLISIS EN TIEMPO REAL ACTIVO**\n\n"
                "🔴 **Estado actual:** Análisis en tiempo real ejecutándose\n\n"
                "🎬 **¿Quieres analizar un video?**\n"
                "Para analizar un video, necesito pausar el análisis en tiempo real.\n\n"
                "📋 **¿Qué pasará?**\n"
                "• ⏸️ Se pausará el análisis en tiempo real\n"
                "• 🎬 Se activará el modo de análisis de video\n"
                "• 🔄 Podrás reanudar tiempo real después\n\n"
                "¿Quieres continuar?",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            return
        
        # Si no hay análisis en tiempo real activo, proceder normalmente
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
                [InlineKeyboardButton("📸 Ver Ahora", callback_data="capture_frame")],
                [InlineKeyboardButton("⏹️ Detener", callback_data="stop_realtime")],
                [InlineKeyboardButton("🎬 Cambiar a Video", callback_data="switch_to_video")],
                [InlineKeyboardButton("🏠 Menú", callback_data="show_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.callback_query.message.reply_text(
                "🚀 **ANÁLISIS EN TIEMPO REAL INICIADO**\n\n"
                "✅ Cámara activada\n"
                "📹 Analizando video en vivo\n"
                "🔔 Alertas automáticas activadas\n"
                "📸 Función de captura instantánea disponible\n\n"
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
        """Worker que ejecuta el análisis en tiempo real usando EXACTAMENTE la misma lógica que la opción 2 de la consola"""
        try:
            logger.info("📹 Iniciando análisis en tiempo real desde Telegram (usando lógica de consola)...")
            
            import cv2
            import time
            import os
            
            # Encontrar cámara disponible (misma función que main.py)
            camera_index = self._find_available_camera()
            if camera_index is None:
                logger.error("❌ No se encontró ninguna cámara")
                self._send_error_to_chat(chat_id, "❌ No se encontró ninguna cámara disponible")
                return
            
            # Inicializar componentes (exactamente como en main.py)
            try:
                logger.info("🧠 Cargando modelo de IA...")
                from .cam_utils import EmotionDetector
                detector = EmotionDetector("modelo/mejor_modelo_83.h5")
                logger.info("✅ Modelo de emociones cargado exitosamente")
            except Exception as e:
                logger.error(f"❌ Error cargando modelo: {e}")
                self._send_error_to_chat(chat_id, f"❌ Error cargando modelo: {e}")
                return
            
            try:
                logger.info("🐕 Inicializando detector YOLO optimizado...")
                from .yolo_dog_detector import YoloDogDetector
                yolo_detector = YoloDogDetector(confidence_threshold=0.60)
                logger.info("✅ YOLOv8 cargado exitosamente (umbral: 60%)")
            except Exception as e:
                logger.error(f"❌ Error cargando YOLO: {e}")
                self._send_error_to_chat(chat_id, f"❌ Error cargando YOLO: {e}")
                return
            
            # Inicializar cámara (EXACTO como en main.py)
            cap = cv2.VideoCapture(camera_index)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            cap.set(cv2.CAP_PROP_FPS, 30)
            
            if not cap.isOpened():
                logger.error("❌ No se pudo abrir la cámara")
                self._send_error_to_chat(chat_id, "❌ No se pudo abrir la cámara")
                return
            
            # Notificar éxito
            logger.info("✅ Análisis en tiempo real iniciado correctamente")
            self._send_status_to_chat(chat_id, "✅ **ANÁLISIS EN TIEMPO REAL INICIADO**\n\n🖥️ **Una ventana de cámara se abrió en tu PC**\n\n🎮 **Controles:**\n• Q o ESC: Salir\n• Telegram: Control remoto")
            
            # Variables de control (EXACTAS como en main.py)
            emotion_history = []
            cooldown_time = 2  # Reducido a 2 segundos para mejor responsividad
            last_analysis_time = time.time()
            frame_count = 0
            
            logger.info("\n🎮 CONTROLES:")
            logger.info("  Q o ESC: Salir")
            logger.info("  Telegram: Control remoto completo")
            logger.info("\n▶️ Iniciando detección...\n")
            
            # BUCLE PRINCIPAL - COPIA EXACTA DE run_camera_analysis en main.py
            try:
                while self.realtime_active and not self.realtime_stop_flag:
                    ret, frame = cap.read()
                    if not ret:
                        logger.error("Error capturando frame")
                        break

                    current_time = time.time()
                    frame_count += 1
                    
                    # Actualizar frame actual para captura remota (thread-safe)
                    with self.frame_lock:
                        self.current_frame = frame.copy()
                    
                    # PASO 1: Detectar perros con YOLO
                    dog_detections = yolo_detector.detect_dogs(frame)
                    dogs_detected = yolo_detector.is_dog_detected(dog_detections)
                    
                    # PASO 2: Dibujar detecciones de YOLO solamente
                    frame = yolo_detector.draw_detections(frame, dog_detections)
                    
                    # PASO 3: Solo analizar emociones SI hay perros detectados
                    if dogs_detected and current_time - last_analysis_time >= cooldown_time:
                        try:
                            logger.info(f"🐕 Analizando emociones... (perro detectado)")
                            emotion, prob, preds = detector.predict_emotion(frame)
                            
                            # Debug: Mostrar todas las predicciones para entender el problema
                            logger.info("📊 Análisis detallado de emociones:")
                            for label, p in zip(detector.labels, preds):
                                logger.info(f"  {label}: {p:.4f} ({'⭐' if p == max(preds) else ''})")
                            logger.info(f"  🎯 Resultado final: {emotion.upper()} ({prob:.3f})")
                            
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
                            self.update_emotion_history(emotion)

                            # Verificar patrones preocupantes (reducido a 3 análisis negativos de 4)
                            if len(emotion_history) >= 3 and all(e in ['sad', 'angry'] for e in emotion_history[-3:]):
                                logger.warning(f"🚨 Patrón preocupante detectado: {emotion} repetidamente")
                                
                                try:
                                    # Capturar imagen para la alerta
                                    timestamp = int(time.time())
                                    path = f"alerta_{emotion}_{timestamp}_{int(prob*100)}.jpg"
                                    cv2.imwrite(path, frame)
                                    
                                    # Enviar alerta con recomendaciones (función que ya existe)
                                    self.send_alert(emotion, prob, image_path=path)
                                    
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
                    
                    # Controles para Telegram
                    cv2.putText(frame, 'Q: salir | Telegram: control remoto', (10, info_y + 60), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)

                    cv2.imshow('🐕 FeeliPetAI + YOLOv8', frame)

                    # Manejar teclas
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord('q') or key == 27:  # Q o ESC
                        logger.info("👋 Saliendo del análisis en tiempo real...")
                        self.realtime_stop_flag = True
                        break

            except KeyboardInterrupt:
                logger.info("⚠️ Interrupción por usuario")
            except Exception as e:
                logger.error(f"❌ Error en bucle principal: {e}")
                
        except Exception as e:
            logger.error(f"❌ Error en worker de análisis: {e}")
            self._send_error_to_chat(chat_id, f"❌ Error en análisis: {str(e)[:50]}...")
        finally:
            # Cleanup (exacto como en main.py)
            try:
                if 'cap' in locals():
                    cap.release()
                cv2.destroyAllWindows()
                
                logger.info("🏁 Análisis en tiempo real terminado exitosamente")
                self._send_status_to_chat(chat_id, "🏁 **ANÁLISIS TERMINADO**\n\nLa ventana de cámara se ha cerrado.\n\nUsa el menú para iniciar nuevamente.")
                
            except Exception as cleanup_error:
                logger.error(f"Error en cleanup: {cleanup_error}")
                
            # Resetear estado
            self.realtime_active = False
            self.realtime_stop_flag = False
            self.current_mode = "menu"
            
            # Limpiar frame actual
            with self.frame_lock:
                self.current_frame = None

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
        await self._start_realtime_analysis(update, context)

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

    async def _capture_current_frame(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Capturar y enviar frame actual con análisis"""
        try:
            import cv2  # Import necesario para el procesamiento de frames
            import os   # Import para manejo de archivos temporales
            logger.info("📸 Solicitud de captura de frame desde Telegram...")
            
            if not self.realtime_active:
                keyboard = [[InlineKeyboardButton("🏠 Regresar al Menú", callback_data="show_menu")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.callback_query.message.reply_text(
                    "⚠️ **ANÁLISIS NO ACTIVO**\n\n"
                    "El análisis en tiempo real no está ejecutándose.\n"
                    "Inicia el análisis para poder capturar frames.",
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
                return
            
            # Obtener frame actual de forma thread-safe
            current_frame = None
            with self.frame_lock:
                if self.current_frame is not None:
                    current_frame = self.current_frame.copy()
            
            if current_frame is None:
                keyboard = [[InlineKeyboardButton("🔄 Reintentar", callback_data="capture_frame"),
                           InlineKeyboardButton("🏠 Menú", callback_data="show_menu")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.callback_query.message.reply_text(
                    "⚠️ **NO HAY FRAME DISPONIBLE**\n\n"
                    "El sistema aún no ha capturado ningún frame.\n"
                    "Espera unos segundos e intenta nuevamente.",
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
                return
            
            # Procesar frame con análisis completo
            try:
                # Cargar detectores si no están cargados
                from .cam_utils import EmotionDetector
                from .yolo_dog_detector import YoloDogDetector
                
                detector = EmotionDetector("modelo/mejor_modelo_83.h5")
                yolo_detector = YoloDogDetector(confidence_threshold=0.60)
                
                # Detectar perros
                dog_detections = yolo_detector.detect_dogs(current_frame)
                dogs_detected = yolo_detector.is_dog_detected(dog_detections)
                
                # Dibujar detecciones YOLO
                processed_frame = yolo_detector.draw_detections(current_frame, dog_detections)
                
                # Análisis de emociones si hay perros
                analysis_text = "🔍 **ANÁLISIS INSTANTÁNEO**\n\n"
                
                if dogs_detected:
                    try:
                        emotion, prob, preds = detector.predict_emotion(processed_frame)
                        
                        # Determinar color y dibujar emoción en frame
                        color = (0, 255, 0)  # Verde por defecto
                        if emotion in ['angry', 'sad']:
                            color = (0, 0, 255)  # Rojo para negativas
                        elif emotion == 'happy':
                            color = (0, 255, 255)  # Amarillo para feliz
                        
                        # Dibujar emoción en el frame
                        emotion_text = f'EMOCION: {emotion.upper()} ({prob:.2f})'
                        best_detection = yolo_detector.get_best_dog_region(dog_detections)
                        if best_detection:
                            x, y, w, h = best_detection
                            cv2.putText(processed_frame, emotion_text, (x, y + h + 30), 
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
                        else:
                            cv2.putText(processed_frame, emotion_text, (50, 120), 
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
                        
                        # Texto del análisis
                        emoji_map = {"happy": "😊", "sad": "😢", "angry": "😠", "relaxed": "😌"}
                        emoji = emoji_map.get(emotion, "🐕")
                        
                        analysis_text += f"🐕 **Perros detectados:** {len(dog_detections)}\n"
                        analysis_text += f"{emoji} **Emoción:** {emotion.upper()}\n"
                        analysis_text += f"📊 **Confianza:** {prob:.1%}\n\n"
                        
                        # Recomendaciones
                        recommendations = self.get_recommendations(emotion)
                        if recommendations:
                            analysis_text += "💡 **Recomendación:**\n"
                            analysis_text += recommendations[0] if len(recommendations) > 0 else ""
                        
                    except Exception as e:
                        logger.error(f"Error en análisis de emoción: {e}")
                        analysis_text += "⚠️ Error analizando emoción\n"
                        analysis_text += f"🐕 **Perros detectados:** {len(dog_detections)}"
                else:
                    analysis_text += "🔍 **Estado:** Esperando detección de perro\n"
                    analysis_text += "💡 **Tip:** Asegúrate de que tu mascota esté visible en la cámara"
                    
                    # Dibujar mensaje en frame
                    cv2.putText(processed_frame, 'ESPERANDO DETECCION DE PERRO...', 
                               (50, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                
                # Agregar timestamp al frame
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cv2.putText(processed_frame, f'Captura: {timestamp}', 
                           (10, processed_frame.shape[0] - 10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                
                # Guardar frame temporalmente
                temp_path = f"temp_capture_{int(time.time())}.jpg"
                cv2.imwrite(temp_path, processed_frame)
                
                # Enviar imagen con análisis
                analysis_text += f"\n⏰ **Capturado:** {timestamp}"
                success = self.send_image_with_caption_to_user(temp_path, analysis_text, update.callback_query.message.chat_id)
                
                # Limpiar archivo temporal
                try:
                    os.remove(temp_path)
                except:
                    pass
                
                if success:
                    # Botones de seguimiento
                    keyboard = [
                        [InlineKeyboardButton("📸 Capturar Otra", callback_data="capture_frame")],
                        [InlineKeyboardButton("⏸️ Pausar Análisis", callback_data="pause_realtime")],
                        [InlineKeyboardButton("🏠 Menú", callback_data="show_menu")]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    await update.callback_query.message.reply_text(
                        "✅ **CAPTURA ENVIADA**\n\n"
                        "📸 Frame capturado con análisis completo\n"
                        "🔄 El análisis en tiempo real continúa\n\n"
                        "Puedes capturar otra imagen cuando gustes.",
                        reply_markup=reply_markup,
                        parse_mode='Markdown'
                    )
                    logger.info("📸 Frame capturado y enviado exitosamente")
                else:
                    raise Exception("Error enviando imagen")
                    
            except Exception as analysis_error:
                logger.error(f"Error procesando frame: {analysis_error}")
                
                # Enviar frame sin análisis como respaldo
                temp_path = f"temp_simple_{int(time.time())}.jpg"
                cv2.imwrite(temp_path, current_frame)
                
                simple_caption = (
                    "📸 **CAPTURA DE CÁMARA**\n\n"
                    "⚠️ Frame capturado sin análisis detallado\n"
                    f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                    "El sistema continúa funcionando normalmente."
                )
                
                self.send_image_with_caption_to_user(temp_path, simple_caption, update.callback_query.message.chat_id)
                
                try:
                    os.remove(temp_path)
                except:
                    pass
                
                keyboard = [[InlineKeyboardButton("🔄 Reintentar", callback_data="capture_frame"),
                           InlineKeyboardButton("🏠 Menú", callback_data="show_menu")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await update.callback_query.message.reply_text(
                    "⚠️ **CAPTURA PARCIAL**\n\n"
                    "Se capturó la imagen pero hubo un problema con el análisis.\n"
                    "El sistema sigue funcionando normalmente.",
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
                
        except Exception as e:
            logger.error(f"❌ Error general en captura de frame: {e}")
            
            keyboard = [[InlineKeyboardButton("🔄 Reintentar", callback_data="capture_frame"),
                       InlineKeyboardButton("🏠 Menú", callback_data="show_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.callback_query.message.reply_text(
                "❌ **ERROR EN CAPTURA**\n\n"
                "No se pudo capturar el frame actual.\n"
                "Verifica que el análisis esté ejecutándose correctamente.",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )

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

    def send_image_with_caption_to_user(self, image_path, caption, target_chat_id):
        """Envía una imagen con texto a un chat específico (multiusuario)"""
        try:
            logger.info(f"📸 Enviando imagen a chat {target_chat_id}: {image_path}")
            
            url = f"https://api.telegram.org/bot{self.token}/sendPhoto"
            
            with open(image_path, 'rb') as photo:
                files = {'photo': photo}
                data = {
                    'chat_id': target_chat_id,  # Chat específico del usuario
                    'caption': caption,
                    'parse_mode': 'Markdown'
                }
                
                response = requests.post(url, files=files, data=data, timeout=15)
                
                if response.status_code == 200:
                    logger.info(f"✅ Imagen enviada exitosamente a chat {target_chat_id}")
                    return True
                else:
                    logger.error(f"❌ Error enviando imagen a chat {target_chat_id}: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Error enviando imagen a chat {target_chat_id}: {e}")
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

    def _get_current_time(self):
        """Obtiene la hora actual formateada"""
        return datetime.now().strftime("%H:%M:%S")

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
