# 🐕 Dog Emotion AI - Aplicación Web

**Análisis Emocional de Mascotas con Inteligencia Artificial**

Una aplicación web moderna y futurista para analizar las emociones de perros utilizando Deep Learning y Computer Vision avanzado.

## 🚀 Características Principales

### ✨ Funcionalidades Core
- **Análisis en Tiempo Real**: Usa tu cámara web para análisis instantáneo
- **Subida de Archivos**: Analiza fotos y videos de tu mascota
- **Sistema Freemium**: 5 análisis gratuitos, premium ilimitado
- **Pago Simulado**: Sistema de pago de demostración ($5/mes)
- **Bot de Telegram**: Acceso premium al bot personalizado
- **Interfaz Futurista**: Diseño moderno con efectos 3D y partículas

### 🧠 Tecnología IA
- **Emociones Detectadas**: Feliz 😊, Triste 😢, Enojado 😡, Relajado 😌
- **Precisión**: 96.3% en detección emocional
- **Modelos**: TensorFlow/Keras + YOLOv8 para detección de perros
- **Procesamiento**: Tiempo real con OpenCV

## 🔧 Instalación y Configuración

### 1. Clonar el Repositorio
```bash
git clone <url-del-repositorio>
cd ProyectoIA-EmocionesPerros
```

### 2. Instalar Dependencias
```bash
pip install -r requirements.txt
```

### 3. Verificar Modelos de IA
Asegúrate de que estos archivos estén presentes:
- `modelo/mejor_modelo_83.h5` - Modelo de emociones
- `yolov8n.pt` - Modelo YOLO para detección de perros

### 4. Ejecutar la Aplicación
```bash
python main.py
```

## 🌐 Uso de la Aplicación Web

### Inicio Rápido
1. **Ejecutar**: `python main.py`
2. **Abrir**: http://localhost:5000 en tu navegador
3. **Probar**: Hasta 5 análisis gratuitos
4. **Premium**: Simular pago para acceso ilimitado

### Flujo de Usuario

#### 🆓 Versión Gratuita (5 análisis)
1. **Seleccionar Método**:
   - 📹 Cámara en tiempo real
   - 📁 Subir archivos (fotos/videos)

2. **Realizar Análisis**:
   - El sistema detecta perros automáticamente
   - Analiza emociones con IA avanzada
   - Muestra resultados visuales detallados

3. **Ver Resultados**:
   - Emoción dominante con porcentaje de confianza
   - Gráficos de barras de todas las emociones
   - Datos técnicos del análisis

#### 💎 Versión Premium (Después del Pago)
1. **Pago Simulado**:
   - Modal de pago con datos ficticios
   - Procesamiento simulado de $5/mes
   - Confirmación instantánea

2. **Acceso Ilimitado**:
   - Análisis sin límite
   - Acceso al Bot de Telegram
   - Funciones premium desbloqueadas

3. **Bot de Telegram**:
   - QR code para acceso directo
   - Chat personalizado
   - Análisis por Telegram

## 🏗️ Arquitectura del Sistema

### Backend (Flask + SocketIO)
```
app.py                 # Servidor web principal
├── routes/           # Endpoints de la API
├── websocket/        # Conexiones tiempo real  
├── models/           # Inicialización de IA
└── payment/          # Sistema de pago simulado
```

### Frontend (HTML5 + JavaScript)
```
templates/index.html   # Interfaz principal
├── styles/           # CSS futurista
├── particles/        # Sistema de partículas
├── websocket/        # Cliente SocketIO
└── payment/          # Modal de pago
```

### IA y Procesamiento
```
utils/
├── cam_utils.py      # Detector de emociones
├── yolo_dog_detector.py  # Detector de perros
└── telegram_utils.py     # Bot de Telegram
```

## 📱 Funcionalidades Detalladas

### 🎯 Sistema de Análisis
- **Detección de Perros**: YOLOv8 con 60% de confianza mínima
- **Análisis Emocional**: Red neuronal CNN personalizada
- **Tiempo Real**: Procesamiento a 30 FPS
- **Formatos Soportados**: JPG, PNG, MP4, AVI, MOV

### 🎨 Interfaz de Usuario
- **Diseño Futurista**: Glassmorphism y efectos neón
- **Animaciones**: Partículas interactivas y transiciones suaves
- **Responsive**: Compatible con móviles y tablets
- **Accesibilidad**: Controles de teclado y navegación clara

### 💳 Sistema de Pago
- **Demo Completa**: Simulación realista de pago
- **Validación**: Formulario con validación de tarjeta
- **Procesamiento**: Animación de carga y confirmación
- **Premium**: Desbloqueo instantáneo de funciones

### 📊 Analytics y Datos
- **Contador por IP**: Límite de 5 análisis por usuario
- **Historial**: Registro de análisis realizados
- **Estadísticas**: Confianza, emociones detectadas
- **Exportación**: Datos descargables (próximamente)

## 🔧 Configuración Avanzada

### Variables de Entorno
```bash
# Telegram Bot (opcional)
TELEGRAM_TOKEN=tu_token_aqui
TELEGRAM_CHAT_ID=tu_chat_id_aqui

# Configuración del servidor
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
FLASK_DEBUG=False
```

### Personalización
- **Límite de Análisis**: Modificar `ANALYSIS_LIMIT` en `app.py`
- **Precio Premium**: Cambiar en el modal de pago
- **Emociones**: Ajustar labels en `cam_utils.py`
- **Diseño**: Modificar variables CSS en `index.html`

## 🧪 Modo de Desarrollo

### Sin Modelos de IA
Si los modelos no están disponibles, la aplicación funciona en modo demo:
- Datos simulados para análisis
- Todas las funciones de UI activas
- Ideal para desarrollo frontend

### Debug y Logs
```bash
# Ver logs en tiempo real
tail -f dog_emotion_ai.log

# Ejecutar con debug
python main.py --debug
```

## 📋 Resolución de Problemas

### Errores Comunes

#### 1. "Modelo no encontrado"
```bash
# Verificar archivos
ls modelo/mejor_modelo_83.h5
ls yolov8n.pt
```

#### 2. "Dependencias faltantes"
```bash
# Reinstalar dependencias
pip install -r requirements.txt --upgrade
```

#### 3. "Cámara no disponible"
- Verificar permisos de cámara en el navegador
- Probar con archivos de video/imagen
- Usar modo de desarrollo

#### 4. "Puerto 5000 en uso"
```bash
# Encontrar proceso
lsof -i :5000
# Cambiar puerto en app.py
```

## 🚀 Despliegue en Producción

### Configuración Básica
```bash
# Usar servidor WSGI
pip install gunicorn
gunicorn --worker-class eventlet -w 1 app:app
```

### Docker (Opcional)
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["python", "main.py"]
```

## 📞 Soporte y Contacto

### Equipo de Desarrollo
- **IA Specialist**: Desarrollo de modelos de Deep Learning
- **Full Stack Dev**: Aplicación web y backend
- **Veterinary Consultant**: Validación de comportamiento animal
- **Data Analyst**: Análisis de resultados y métricas

### Contacto
- **Email**: info@dogemotionai.com
- **Web**: http://localhost:5000
- **Issues**: Reportar problemas en el repositorio

## 📄 Licencia

Este proyecto está bajo la licencia MIT. Ver `LICENSE` para más detalles.

---

**© 2024 Dog Emotion AI Team** | Desarrollado con ❤️ para nuestros amigos peludos 🐕