# 🐕 Monitor de Emociones Caninas con IA

Sistema inteligente para detectar y monitorear el estado emocional de perros usando visión por computadora y notificaciones automáticas vía Telegram.

## � Características

- 🎯 **Detección de emociones en tiempo real** usando YOLO y análisis facial
- 📸 **Captura automática de imágenes** cuando se detectan emociones
- 🤖 **Bot de Telegram interactivo** con menú y alertas automáticas
- 📊 **Historial y estadísticas** de comportamiento emocional
- 💡 **Recomendaciones personalizadas** según la emoción detectada
- 🔔 **Alertas automáticas** cuando se detectan patrones preocupantes

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
1. **Abre Telegram** y busca el bot: **@Emocionesperrunasbot**
   
   O usa este enlace directo: **[t.me/Emocionesperrunasbot](https://t.me/Emocionesperrunasbot)**

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

### Método 1: Ejecutable Simple (Recomendado)

**Doble clic en `ejecutar.bat`** - ¡Eso es todo!

El archivo `.bat` automáticamente:
- Activa el entorno virtual
- Ejecuta el sistema principal
- Mantiene la ventana abierta para ver logs

### Método 2: Terminal Manual

```cmd
# 1. Activar entorno virtual
.venv\Scripts\activate

# 2. Ejecutar sistema principal
python main.py
```

### Método 3: Desarrollo/Debug

```cmd
# Para desarrolladores que quieren ver logs detallados
python main.py --debug
```

## 🤖 Usando el Bot de Telegram

### Comandos Principales

| Comando | Descripción |
|---------|-------------|
| `/start` | Inicializar el bot y mostrar bienvenida |
| `/menu` | Mostrar menú principal interactivo |
| `/status` | Ver estado emocional actual de tu mascota |

### Menú Interactivo

El bot incluye un menú con botones para:

- 📊 **Estado Actual** - Ver última emoción detectada
- 📈 **Resumen del Día** - Estadísticas completas
- 🔔 **Activar/Pausar Monitoreo** - Controlar alertas automáticas
- 💡 **Consejos Generales** - Recomendaciones de cuidado
- 🧹 **Limpiar Chat** - Eliminar mensajes del bot
- ❓ **Ayuda** - Información de comandos

### Alertas Automáticas

Cuando el sistema detecta patrones emocionales importantes:

- 🚨 **Alerta instantánea** con imagen capturada
- 📝 **Análisis detallado** de la emoción detectada
- 💡 **Recomendaciones específicas** para esa emoción
- 📊 **Nivel de confianza** del análisis

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
- EVerifica que e TOKEN yssdcorrectao- Asegúrate de haber enviado `/start` alb u@ot
- Confirma que telChat ID etr tnlconrntc
o
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

- ⚡ **Rendimiento**: Requiere cámara USB o integrada funcional
- 💾 **Almacenamiento**: Las imágenes se guardan temporalmente en formato JPG
- 🔋 **Recursos**: Usa procesamiento de CPU, puede consumir batería en laptops
- 🌐 **Internet**: Requiere conexión para enviar notificaciones por Telegram
- 🐕 **Compatibilidad**: Optimizado para perros, puede detectar otros animales con menor precisión

## 🆘 Soporte

Si encuentras problemas:

1. **Revisa los logs** en la terminal para errores específicos
2. **Verifica la configuración** de Telegram (Token y Chat ID)
3. **Prueba la cámara** independientemente
4. **Consulta esta guía** para configuración paso a paso

## 📄 Licencia

Proyecto educativo - Uso libre para aprendizaje y desarrollo.

---

**🎯 ¡Tu sistema está listo para monitorear el bienestar emocional de tu mascota las 24 horas!**
