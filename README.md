# 🐕 Monitor de Emociones Caninas con IA

Sistema inteligente para detectar y monitorear el estado emocional de perros usando visión por computadora, análisis en tiempo real y control completo vía Telegram.

## ✨ Características Principales

- 🎯 **Detección de emociones en tiempo real** usando YOLOv8 y análisis facial avanzado
- � **Análisis de videos** con estadísticas completas y reportes detallados
- 🖥️ **Ventana visual en tiempo real** con detecciones superpuestas y controles
- 🤖 **Bot de Telegram completo** con navegación intuitiva y control remoto
- 👥 **Sistema multiusuario** - cada usuario maneja su sesión independiente
- 🎮 **Control dual** - manejo desde PC (teclado) y Telegram simultáneamente
- 📊 **Estadísticas detalladas** de comportamiento emocional
- 🔔 **Alertas automáticas** cuando se detectan emociones preocupantes
- 🏠 **Navegación mejorada** con botones "Regresar al Menú" en todas las funciones

## 🚀 Nuevas Funcionalidades (Actualización Reciente)

### 📱 **Bot de Telegram Mejorado**
- ✅ **Navegación intuitiva** con botones contextuales
- ✅ **Análisis de videos** subiendo archivos directamente
- ✅ **Control de análisis en tiempo real** desde el chat
- ✅ **Estadísticas completas** con emociones detectadas, confianza promedio y más
- ✅ **Sistema multiusuario** robusto

### 🎥 **Análisis en Tiempo Real Avanzado**
- ✅ **Ventana visual** que se abre en tu PC mostrando la cámara
- ✅ **Detecciones en vivo** con bounding boxes y emociones superpuestas
- ✅ **Controles por teclado** (Q=pausar, ESC=detener)
- ✅ **Control remoto desde Telegram** (pausa/reanudación/detener)
- ✅ **Colores por emoción** (Verde=feliz, Amarillo=relajado, Rojo=triste/enojado)

### � **Análisis de Videos**
- ✅ **Subida directa desde Telegram** (MP4, AVI, MOV)
- ✅ **Procesamiento completo** con estadísticas detalladas
- ✅ **Video de salida** con detecciones marcadas
- ✅ **Resumen estadístico** (total emociones, distribución, confianza promedio)

## 🚀 Instalación y Configuración (Primera Vez)

### Paso 1: Preparar el entorno

1. **Extraer el archivo ZIP** en una carpeta de tu elección
2. **Abrir terminal/cmd** en la carpeta del proyecto
3. **Crear entorno virtual Python**:
   ```cmd
   python -m venv .venv
   ```
4. **Activar el entorno virtual**:
   ```cmd
   .venv\Scripts\activate
   ```
5. **Instalar dependencias**:
   ```cmd
   pip install -r requirements.txt
   ```

### Paso 2: Configurar el Bot de Telegram

#### 2.1 Conectar con el Bot Preconfigurado

**🤖 Bot de Telegram: @Emocionesperrunasbot**

<div align="center">
  <img src="LandingPage/assets/images/CodigoQr/Codigo.jpg" alt="Código QR del Bot" width="200">
  
  **Escanea el código QR o usa el enlace directo:**
  
  **[t.me/Emocionesperrunasbot](https://t.me/Emocionesperrunasbot)**
</div>

**Pasos para conectar:**

1. **Escanea el código QR** con tu app de Telegram o busca manualmente: **@Emocionesperrunasbot**

2. **Envía `/start`** para inicializar el bot

3. **Copia tu Chat ID** que aparece en el mensaje de bienvenida

#### 2.2 Obtener tu Chat ID (Método alternativo)
Si necesitas obtener tu Chat ID manualmente:

1. **Ejecuta el script incluido**:
   ```cmd
   python get_chat_id.py
   ```
2. **Presiona Enter** para usar el bot preconfigurado
3. **Envía cualquier mensaje** al bot @Emocionesperrunasbot
4. **Copia el Chat ID** que se muestra en la terminal

#### 2.3 Configurar tu Chat ID
1. **Edita el archivo `main.py`**
2. **Busca esta línea** (cerca del final del archivo):
   ```python
   TELEGRAM_CHAT_ID = "TU_CHAT_ID_AQUI"
   ```
3. **Reemplaza** con tu Chat ID real:
   ```python
   TELEGRAM_CHAT_ID = "123456789"  # Tu Chat ID obtenido del bot
   ```

   **⚠️ IMPORTANTE**: NO cambies el `TELEGRAM_TOKEN`, ya está configurado para el bot oficial.

### Paso 3: Verificar la instalación

**Ejecuta el test de conexión**:
```cmd
python test_image_quick.py
```

Si todo está bien configurado, deberías recibir:
- ✅ Un mensaje de prueba en tu bot de Telegram
- ✅ Logs exitosos en la terminal

## 🎮 Cómo Usar la Aplicación

### Método Principal: Bot de Telegram (Recomendado)

1. **Ejecutar el sistema**:
   ```cmd
   python main.py
   ```
   O doble clic en `ejecutar.bat`

2. **En Telegram**, envía `/start` al bot @Emocionesperrunasbot

3. **Usa el menú interactivo**:
   - 📹 **Analizar Video** - Sube un video y recibe análisis completo
   - 🎥 **Análisis en Tiempo Real** - Activa la cámara con ventana visual
   - 🏠 **Regresar al Menú** - Disponible en todas las funciones

### Funcionalidades del Bot

#### 📹 **Análisis de Videos**
- Sube videos directamente al chat (MP4, AVI, MOV)
- Recibe estadísticas completas: emociones detectadas, confianza, distribución
- Descarga el video procesado con detecciones marcadas

#### 🎥 **Análisis en Tiempo Real**
- Se abre una ventana en tu PC mostrando la cámara
- Detecciones de perros con bounding boxes verdes
- Emociones superpuestas con colores (Verde=feliz, Rojo=triste/enojado)
- **Control por teclado**: Q (pausar), ESC (detener)
- **Control desde Telegram**: Botones de pausa/reanudación/detener

#### 👥 **Sistema Multiusuario**
- Cada usuario tiene su sesión independiente
- No interfiere con otros usuarios del mismo bot
- Gestión automática de recursos por usuario

### Método Alternativo: Solo Consola

Si prefieres usar solo la consola sin Telegram:

```cmd
python main.py
# Selecciona opción 2: "Cámara en tiempo real desde consola"
# O opción 3: "Procesar archivo de video desde consola"
```

## 🤖 Bot de Telegram - Comandos y Funciones

### Comandos Principales

| Comando | Descripción |
|---------|-------------|
| `/start` | Inicializar el bot y mostrar menú principal |
| `/menu` | Mostrar menú interactivo con todas las opciones |

### Menú Interactivo Completo

#### 📊 **Análisis y Monitoreo**
- 📹 **Analizar Video** - Sube videos para análisis completo con estadísticas
- 🎥 **Análisis en Tiempo Real** - Activa cámara con ventana visual en PC
- � **Ver Estadísticas** - Resumen de análisis realizados

#### 🎮 **Controles de Tiempo Real**
- ⏸️ **Pausar** - Pausa el análisis en tiempo real manteniendo la sesión
- ▶️ **Reanudar** - Continúa el análisis pausado
- ⏹️ **Detener** - Termina completamente el análisis y libera recursos

#### 🔔 **Gestión de Alertas**
- 🔔 **Activar Monitoreo** - Habilita alertas automáticas por emociones
- � **Pausar Monitoreo** - Desactiva alertas temporalmente
- ⚙️ **Configurar Alertas** - Ajusta sensibilidad y tipos de alertas

#### 🛠️ **Utilidades**
- 🏠 **Regresar al Menú** - Disponible en todas las funciones para navegación fácil
- 🧹 **Limpiar Chat** - Elimina mensajes del bot para mantener el chat limpio
- ❓ **Ayuda** - Información detallada de comandos y funciones

### Alertas Automáticas Mejoradas

El sistema envía notificaciones inteligentes cuando detecta:

- 🚨 **Emociones negativas** (tristeza, enojo) con alta confianza
- 📊 **Patrones de comportamiento** preocupantes
- 🎯 **Análisis detallado** con nivel de confianza y recomendaciones
- 📸 **Capturas automáticas** del momento de la detección

## 📁 Estructura del Proyecto

```
ProyectoIACam/
├── main.py                 # Sistema principal de detección
├── ejecutar.bat           # Ejecutable simple para Windows
├── get_chat_id.py         # Script para obtener Chat ID de Telegram
├── requirements.txt       # Dependencias Python
├── README.md             # Esta guía
├── modelo/
│   └── mejor_modelo_83.h5 # Modelo de IA entrenado
└── utils/
    ├── cam_utils.py      # Utilidades de cámara y YOLO
    └── telegram_utils.py # Bot de Telegram y notificaciones
```

## 🤖 Bot de Telegram Preconfigurado

**Bot oficial**: [@Emocionesperrunasbot](https://t.me/Emocionesperrunasbot)

- ✅ **Ya configurado** y listo para usar
- ✅ **Token incluido** en el código
- ✅ **Solo necesitas** configurar tu Chat ID
- ✅ **Funciones completas** de monitoreo y alertas

## 🔧 Configuración Avanzada

### Ajustar Sensibilidad de Detección

En `main.py`, puedes modificar:

```python
# Umbral de confianza para detección de emociones (0.0 - 1.0)
CONFIDENCE_THRESHOLD = 0.7  # Más alto = más estricto

# Frecuencia de análisis (frames entre análisis)
ANALYSIS_INTERVAL = 30  # Más alto = menos frecuente

# Número de detecciones consecutivas para activar alerta
ALERT_THRESHOLD = 3  # Más alto = menos alertas
```

### Configurar Cámara

Por defecto usa la cámara 0. Para cambiar:

```python
# En main.py, línea de inicialización de cámara
cap = cv2.VideoCapture(1)  # Cambiar 0 por el número de tu cámara
```

## 🔍 Solución de Problemas

### ❌ "No se reconoce 'python'"
**Solución**: Instala Python desde [python.org](https://python.org) y asegúrate de marcar "Add to PATH"

### ❌ "No se encuentra la cámara"
**Solución**:
- Verifica que tu cámara esté conectada
- Prueba cambiar el número de cámara en `main.py`
- Otorga permisos de cámara a Python

### ❌ "Error de Telegram: Unauthorized"
**Solución**:
- Verifica que el TOKEN sea correcto
- Asegúrate de haber enviado `/start` al bot
- Confirma que el Chat ID esté en la lista de usuarios

### ❌ "No detecta al perro"
**Solución**:
- Asegúrate de que haya buena iluminación
- El perro debe estar visible en la cámara
- Ajusta el umbral de confianza más bajo

### ❌ "No recibo alertas"
**Solución**:
- Verifica que el monitoreo esté activo (`/menu` → "Activar Monitoreo")
- Revisa que las notificaciones de Telegram estén habilitadas
- Confirma que el sistema esté detectando emociones

## 📝 Notas Importantes

- ⚡ **Rendimiento**: Sistema optimizado para análisis en tiempo real
- 💾 **Almacenamiento**: Videos procesados se guardan automáticamente
- 🔋 **Recursos**: Uso moderado de CPU/RAM, optimizado para laptops
- 🌐 **Internet**: Solo requiere conexión para Telegram
- 🐕 **Compatibilidad**: Entrenado específicamente para perros domésticos
- 🎯 **Precisión**: 83% de accuracy en detección emocional

## 🏆 Rendimiento del Sistema

- **Detección de perros**: YOLOv8 con 95%+ precisión
- **Clasificación emocional**: Modelo custom con 83% accuracy
- **Velocidad**: 15-30 FPS en tiempo real
- **Latencia Telegram**: <2 segundos respuesta promedio
- **Memoria RAM**: ~500MB durante operación

## 🛠️ Tecnologías Utilizadas

- **Computer Vision**: OpenCV + YOLOv8
- **Deep Learning**: TensorFlow/Keras
- **Bot Framework**: python-telegram-bot
- **Interfaz**: Tkinter + CV2 GUI
- **Procesamiento**: NumPy + PIL

---

**Desarrollado con ❤️ para el bienestar canino**

*Sistema completo de monitoreo emocional con tecnología de punta*

1. **Revisa los logs** en la terminal para errores específicos
2. **Verifica la configuración** de Telegram (Token y Chat ID)
3. **Prueba la cámara** independientemente
4. **Consulta esta guía** para configuración paso a paso

## 📄 Licencia

Proyecto educativo - Uso libre para aprendizaje y desarrollo.

---

**🎯 ¡Tu sistema está listo para monitorear el bienestar emocional de tu mascota las 24 horas!**
