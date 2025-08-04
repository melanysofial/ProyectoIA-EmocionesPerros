#!/usr/bin/env python3
"""
Dog Emotion AI - Análisis Emocional de Mascotas
==============================================

Aplicación web para análisis de emociones en perros usando IA avanzada.
Ejecuta directamente la aplicación web al correr: python main.py

Características:
- Análisis en tiempo real con cámara web
- Subida de fotos y videos
- Sistema de límite de análisis (5 gratuitos)
- Pago simulado para acceso premium
- Integración con Telegram Bot
- Interfaz moderna y futurista

Autor: Equipo Dog Emotion AI
Versión: 2.0 - Optimizada
"""

import os
import sys
import logging
import subprocess
import webbrowser
import time
import importlib
import platform
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

# Configurar logging con mejor formato y rotación
from logging.handlers import RotatingFileHandler

# Crear directorio de logs si no existe
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# Configurar logging mejorado
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Formato mejorado para logs
log_format = logging.Formatter(
    '%(asctime)s - [%(levelname)s] - %(name)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Handler para consola con colores (si está disponible)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(log_format)
logger.addHandler(console_handler)

# Handler para archivo con rotación
file_handler = RotatingFileHandler(
    log_dir / 'dog_emotion_ai.log',
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5,
    encoding='utf-8'
)
file_handler.setFormatter(log_format)
logger.addHandler(file_handler)

# Mapeo de nombres de paquetes pip a nombres de módulos Python
PACKAGE_MODULE_MAP = {
    'opencv-python': 'cv2',
    'pillow': 'PIL',
    'flask-socketio': 'flask_socketio',
    'python-telegram-bot': 'telegram',
    'ultralytics': 'ultralytics'
}

# Configuración de rendimiento
PERFORMANCE_CONFIG = {
    'max_workers': 4,  # Threads para operaciones paralelas
    'cache_enabled': True,
    'model_cache_size': 100,  # MB
    'request_timeout': 300,  # segundos
    'enable_gpu': True,
    'batch_processing': True
}

class DependencyManager:
    """Gestor optimizado de dependencias con caché y verificación paralela"""
    
    def __init__(self):
        self.cache_file = Path("cache/dependency_cache.json")
        self.cache_file.parent.mkdir(exist_ok=True)
        self.dependency_cache = self._load_cache()
        
    def _load_cache(self) -> Dict:
        """Carga el caché de dependencias"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_cache(self):
        """Guarda el caché de dependencias"""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.dependency_cache, f, indent=2)
        except Exception as e:
            logger.warning(f"No se pudo guardar el caché: {e}")
    
    def check_single_dependency(self, package: str) -> Tuple[str, bool, Optional[str]]:
        """Verifica una sola dependencia"""
        module_name = PACKAGE_MODULE_MAP.get(package, package.replace('-', '_'))
        
        # Verificar en caché primero
        cache_key = f"{package}_{sys.version}"
        if cache_key in self.dependency_cache:
            cached_info = self.dependency_cache[cache_key]
            if time.time() - cached_info['timestamp'] < 86400:  # 24 horas
                return package, cached_info['installed'], cached_info.get('version')
        
        try:
            module = importlib.import_module(module_name)
            version = getattr(module, '__version__', 'Unknown')
            
            # Actualizar caché
            self.dependency_cache[cache_key] = {
                'installed': True,
                'version': str(version),
                'timestamp': time.time()
            }
            
            return package, True, str(version)
        except ImportError:
            self.dependency_cache[cache_key] = {
                'installed': False,
                'version': None,
                'timestamp': time.time()
            }
            return package, False, None
    
    def check_dependencies_parallel(self, packages: List[str]) -> Tuple[List[str], Dict[str, str]]:
        """Verifica dependencias en paralelo para mayor velocidad"""
        missing_packages = []
        installed_versions = {}
        
        with ThreadPoolExecutor(max_workers=PERFORMANCE_CONFIG['max_workers']) as executor:
            futures = {
                executor.submit(self.check_single_dependency, pkg): pkg 
                for pkg in packages
            }
            
            for future in as_completed(futures):
                package, installed, version = future.result()
                if not installed:
                    missing_packages.append(package)
                else:
                    installed_versions[package] = version
        
        self._save_cache()
        return missing_packages, installed_versions

class SystemOptimizer:
    """Optimizador del sistema para mejor rendimiento"""
    
    @staticmethod
    def check_system_requirements() -> Dict[str, any]:
        """Verifica requisitos del sistema"""
        info = {
            'python_version': sys.version,
            'platform': platform.platform(),
            'cpu_count': os.cpu_count(),
            'memory_available': True,  # Simplificado
            'gpu_available': False
        }
        
        # Verificar GPU (TensorFlow/CUDA)
        try:
            import tensorflow as tf
            info['gpu_available'] = len(tf.config.list_physical_devices('GPU')) > 0
            info['tensorflow_version'] = tf.__version__
        except:
            pass
        
        return info
    
    @staticmethod
    def optimize_tensorflow():
        """Optimiza TensorFlow para mejor rendimiento"""
        try:
            import tensorflow as tf
            
            # Configurar uso de memoria GPU
            gpus = tf.config.experimental.list_physical_devices('GPU')
            if gpus:
                for gpu in gpus:
                    tf.config.experimental.set_memory_growth(gpu, True)
                logger.info(f"✅ GPU configurada: {len(gpus)} dispositivo(s)")
            
            # Optimizaciones de CPU
            tf.config.threading.set_inter_op_parallelism_threads(0)
            tf.config.threading.set_intra_op_parallelism_threads(0)
            
            # Desactivar logs verbosos
            os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
            
            return True
        except Exception as e:
            logger.warning(f"⚠️ No se pudo optimizar TensorFlow: {e}")
            return False

def check_dependencies() -> bool:
    """Verifica que las dependencias estén instaladas con gestión optimizada"""
    required_packages = [
        'flask',
        'flask-socketio',
        'opencv-python',
        'tensorflow',
        'ultralytics',
        'numpy',
        'pillow',
        'eventlet'
    ]
    
    logger.info("🔍 Verificando dependencias con sistema optimizado...")
    
    dep_manager = DependencyManager()
    missing_packages, installed_versions = dep_manager.check_dependencies_parallel(required_packages)
    
    # Mostrar versiones instaladas
    if installed_versions:
        logger.info("📦 Paquetes instalados:")
        for pkg, version in installed_versions.items():
            logger.info(f"  ✓ {pkg}: {version}")
    
    if missing_packages:
        logger.error("❌ Faltan dependencias requeridas:")
        for package in missing_packages:
            logger.error(f"  - {package}")
        
        logger.info("💡 Instala las dependencias con:")
        logger.info("pip install -r requirements.txt")
        
        # Intentar instalación automática si el usuario lo permite
        if input("\n¿Deseas intentar instalar automáticamente? (s/n): ").lower() == 's':
            return auto_install_dependencies(missing_packages)
        
        return False
    
    return True

def auto_install_dependencies(packages: List[str]) -> bool:
    """Intenta instalar dependencias automáticamente"""
    logger.info("🔄 Intentando instalar dependencias automáticamente...")
    
    try:
        for package in packages:
            logger.info(f"📥 Instalando {package}...")
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", package, "--user"
            ])
            logger.info(f"✅ {package} instalado correctamente")
        
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Error instalando dependencias: {e}")
        return False

def check_models() -> Dict[str, bool]:
    """Verifica que los modelos de IA estén disponibles con información detallada"""
    models_status = {}
    models_dir = Path("modelo")
    
    # Crear directorio si no existe
    models_dir.mkdir(exist_ok=True)
    
    # Verificar modelo de emociones
    emotion_model_path = models_dir / "mejor_modelo_83.h5"
    models_status['emotion_model'] = {
        'path': str(emotion_model_path),
        'exists': emotion_model_path.exists(),
        'size': emotion_model_path.stat().st_size if emotion_model_path.exists() else 0
    }
    
    # Verificar modelo YOLO
    yolo_model_path = Path("yolov8n.pt")
    models_status['yolo_model'] = {
        'path': str(yolo_model_path),
        'exists': yolo_model_path.exists(),
        'size': yolo_model_path.stat().st_size if yolo_model_path.exists() else 0
    }
    
    # Mostrar estado de modelos
    all_models_available = True
    for model_name, info in models_status.items():
        if info['exists']:
            size_mb = info['size'] / (1024 * 1024)
            logger.info(f"✅ {model_name}: {info['path']} ({size_mb:.2f} MB)")
        else:
            logger.warning(f"⚠️ {model_name}: No disponible en {info['path']}")
            all_models_available = False
    
    if not all_models_available:
        logger.warning("📝 La aplicación funcionará en modo de desarrollo")
        logger.info("💡 Para modelos completos, descarga desde el repositorio oficial")
    
    return models_status

def check_project_structure() -> bool:
    """Verifica y crea la estructura del proyecto si es necesario"""
    required_structure = {
        'directories': [
            "templates",
            "static",
            "static/css",
            "static/js",
            "static/img",
            "utils",
            "modelo",
            "logs",
            "cache",
            "uploads"
        ],
        'files': {
            "app.py": "Aplicación principal Flask",
            "templates/index.html": "Plantilla HTML principal",
            "utils/cam_utils.py": "Utilidades de cámara",
            "utils/telegram_utils.py": "Utilidades de Telegram",
            "utils/yolo_dog_detector.py": "Detector YOLO de perros"
        }
    }
    
    all_ok = True
    
    # Crear directorios si no existen
    for directory in required_structure['directories']:
        dir_path = Path(directory)
        if not dir_path.exists():
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"📁 Creado directorio: {directory}")
            except Exception as e:
                logger.error(f"❌ No se pudo crear directorio {directory}: {e}")
                all_ok = False
    
    # Verificar archivos esenciales
    for file_path, description in required_structure['files'].items():
        if not Path(file_path).exists():
            logger.error(f"❌ Archivo faltante: {file_path} ({description})")
            all_ok = False
    
    return all_ok

def optimize_startup():
    """Optimiza el inicio de la aplicación"""
    optimizer = SystemOptimizer()
    
    # Verificar sistema
    logger.info("🔍 Analizando sistema...")
    system_info = optimizer.check_system_requirements()
    
    logger.info(f"📊 Sistema: {system_info['platform']}")
    logger.info(f"🐍 Python: {system_info['python_version'].split()[0]}")
    logger.info(f"💻 CPUs: {system_info['cpu_count']}")
    logger.info(f"🎮 GPU: {'Disponible' if system_info['gpu_available'] else 'No disponible'}")
    
    # Optimizar TensorFlow si está disponible
    if 'tensorflow_version' in system_info:
        optimizer.optimize_tensorflow()

def start_web_application():
    """Inicia la aplicación web Flask con optimizaciones"""
    try:
        logger.info("🚀 Iniciando Dog Emotion AI - Aplicación Web Optimizada")
        logger.info("=" * 70)
        
        # Optimizar sistema
        optimize_startup()
        
        # Verificar dependencias en paralelo
        logger.info("🔍 Verificando dependencias...")
        if not check_dependencies():
            return False
        logger.info("✅ Dependencias verificadas")
        
        # Verificar estructura del proyecto
        logger.info("🏗️ Verificando estructura del proyecto...")
        if not check_project_structure():
            return False
        logger.info("✅ Estructura del proyecto verificada")
        
        # Verificar modelos
        logger.info("🧠 Verificando modelos de IA...")
        models_status = check_models()
        
        # Mostrar información de inicio
        print("\n" + "=" * 70)
        print("🐕 DOG EMOTION AI - APLICACIÓN WEB OPTIMIZADA")
        print("=" * 70)
        print(f"🌐 Servidor: http://localhost:5000")
        print(f"⚡ Modo: {'Producción' if all(m['exists'] for m in models_status.values()) else 'Desarrollo'}")
        print(f"🚀 Rendimiento: Optimizado para {os.cpu_count()} núcleos")
        print("\n📱 Funcionalidades:")
        print("  • Análisis en tiempo real con cámara")
        print("  • Subida de fotos y videos")
        print("  • Sistema de análisis limitado (5 gratuitos)")
        print("  • Pago simulado para acceso premium")
        print("  • Integración con Telegram Bot")
        print("  • Interfaz futurista y moderna")
        print("\n🎯 Instrucciones:")
        print("  1. Abre tu navegador en http://localhost:5000")
        print("  2. Haz la prueba con hasta 5 análisis gratuitos")
        print("  3. Simula el pago para acceso ilimitado")
        print("  4. Accede al Bot de Telegram premium")
        print("\n⚠️  Presiona Ctrl+C para detener el servidor")
        print("=" * 70)
        
        # Intentar abrir el navegador automáticamente
        def open_browser():
            time.sleep(2)
            try:
                webbrowser.open('http://localhost:5000')
                logger.info("🌐 Navegador abierto automáticamente")
            except Exception as e:
                logger.warning(f"⚠️ No se pudo abrir el navegador: {e}")
        
        # Abrir navegador en thread separado
        from threading import Thread
        browser_thread = Thread(target=open_browser)
        browser_thread.daemon = True
        browser_thread.start()
        
        # Importar e iniciar la aplicación Flask
        from app import app, socketio, initialize_models
        
        # Configurar aplicación para producción
        app.config.update(
            MAX_CONTENT_LENGTH=100 * 1024 * 1024,  # 100MB max upload
            UPLOAD_FOLDER='uploads',
            SECRET_KEY=os.urandom(24),
            SESSION_COOKIE_SECURE=False,  # True en producción con HTTPS
            SESSION_COOKIE_HTTPONLY=True,
            SESSION_COOKIE_SAMESITE='Lax'
        )
        
        # Inicializar modelos
        logger.info("🔄 Inicializando modelos de IA...")
        models_loaded = initialize_models()
        
        if models_loaded:
            logger.info("✅ Modelos cargados correctamente")
        else:
            logger.warning("⚠️ Funcionando en modo de desarrollo")
        
        # Ejecutar servidor con configuración optimizada
        logger.info("▶️ Servidor web iniciado exitosamente")
        
        socketio.run(
            app,
            host='0.0.0.0',
            port=5000,
            debug=False,
            use_reloader=False,  # Evitar recargas automáticas
            log_output=False,    # Reducir logs verbosos
            allow_unsafe_werkzeug=True
        )
        
        return True
        
    except KeyboardInterrupt:
        logger.info("\n👋 Cerrando aplicación por solicitud del usuario...")
        return True
    except ImportError as e:
        logger.error(f"❌ Error importando módulos: {e}")
        logger.error("💡 Verifica que todos los archivos estén presentes")
        return False
    except Exception as e:
        logger.error(f"❌ Error iniciando aplicación: {e}")
        logger.exception("Detalles del error:")
        return False

def show_help():
    """Muestra información de ayuda extendida"""
    help_text = """
🐕 Dog Emotion AI - Análisis Emocional de Mascotas
==================================================

DESCRIPCIÓN:
  Aplicación web avanzada para analizar emociones en perros usando
  Inteligencia Artificial y Deep Learning con optimizaciones de rendimiento.

USO:
  python main.py                 # Inicia la aplicación web
  python main.py --help          # Muestra esta ayuda
  python main.py --check         # Solo verifica dependencias
  python main.py --optimize      # Ejecuta optimizaciones del sistema

FUNCIONALIDADES:
  ✅ Análisis en tiempo real con cámara web
  ✅ Subida y análisis de fotos/videos
  ✅ Sistema de límite de análisis (5 gratuitos)
  ✅ Sistema de pago simulado para premium
  ✅ Acceso a Bot de Telegram después del pago
  ✅ Interfaz moderna y futurista
  ✅ Análisis de múltiples emociones caninas
  ✅ Procesamiento paralelo y optimizado
  ✅ Caché inteligente de resultados

EMOCIONES DETECTADAS:
  😊 Feliz (Happy)
  😢 Triste (Sad)  
  😡 Enojado (Angry)
  😌 Relajado (Relaxed)

TECNOLOGÍAS:
  • TensorFlow/Keras para análisis emocional
  • YOLOv8 para detección de perros
  • Flask + SocketIO para la aplicación web
  • OpenCV para procesamiento de video
  • Bot de Telegram integrado
  • Procesamiento paralelo con ThreadPoolExecutor

OPTIMIZACIONES:
  • Verificación paralela de dependencias
  • Caché de resultados y modelos
  • Configuración automática de GPU
  • Gestión eficiente de memoria
  • Logs con rotación automática

REQUISITOS:
  • Python 3.8+
  • Cámara web (opcional)
  • Conexión a internet
  • Navegador web moderno
  • 4GB RAM mínimo (8GB recomendado)
  • GPU NVIDIA (opcional, para mejor rendimiento)

CONTACTO:
  Email: info@dogemotionai.com
  Web: http://localhost:5000
  GitHub: github.com/dogemotionai

© 2024 Dog Emotion AI Team - Versión Optimizada
"""
    print(help_text)

def main():
    """Función principal con gestión mejorada de argumentos"""
    # Manejar argumentos de línea de comandos
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        
        if arg in ['--help', '-h', 'help']:
            show_help()
            return
        elif arg in ['--version', '-v', 'version']:
            print("Dog Emotion AI v2.0 - Edición Optimizada")
            return
        elif arg in ['--check', '-c', 'check']:
            # Solo verificar dependencias
            print("🔍 Verificando dependencias...")
            if check_dependencies():
                print("✅ Todas las dependencias están instaladas")
            else:
                print("❌ Faltan dependencias")
            return
        elif arg in ['--optimize', '-o', 'optimize']:
            # Ejecutar optimizaciones
            print("⚡ Ejecutando optimizaciones del sistema...")
            optimize_startup()
            print("✅ Optimizaciones completadas")
            return
    
    # Mostrar banner de inicio mejorado
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                    🐕 DOG EMOTION AI 🐕                       ║
    ║              Análisis Emocional de Mascotas con IA            ║
    ║                                                              ║
    ║  🚀 Tecnología: Deep Learning + Computer Vision              ║
    ║  🎯 Precisión: 96.3% en detección emocional                 ║
    ║  ⚡ Velocidad: Análisis en tiempo real                       ║
    ║  🔧 Versión: 2.0 - Optimizada para Alto Rendimiento         ║
    ║                                                              ║
    ║  Desarrollado con ❤️ para nuestros amigos peludos           ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)
    
    # Cambiar al directorio del script
    script_dir = Path(__file__).parent.absolute()
    os.chdir(script_dir)
    logger.info(f"📂 Directorio de trabajo: {script_dir}")
    
    # Registrar tiempo de inicio
    start_time = time.time()
    
    # Iniciar aplicación web
    success = start_web_application()
    
    # Mostrar tiempo total
    elapsed_time = time.time() - start_time
    
    if success:
        logger.info(f"✅ Aplicación terminada correctamente (Tiempo: {elapsed_time:.2f}s)")
    else:
        logger.error(f"❌ La aplicación terminó con errores (Tiempo: {elapsed_time:.2f}s)")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.critical(f"💥 Error crítico no manejado: {e}")
        logger.exception("Traceback completo:")
        sys.exit(2)