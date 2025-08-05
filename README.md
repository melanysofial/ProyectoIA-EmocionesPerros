# 🐕 Monitor de Emociones Caninas con IA

Sistema inteligente para detectar y monitorear el estado emocional de perros usando visión por computadora, análisis en tiempo real y control completo vía Telegram con **sistema multiusuario por PC**.

## ✨ Características Principales

### 🎯 **Detección Inteligente**
- **YOLOv8** para detección precisa de perros
- **Red neuronal personalizada** (83% precisión) para análisis emocional
- **Análisis en tiempo real** con ventana visual interactiva
- **Procesamiento de videos** con estadísticas completas

### 🤖 **Bot de Telegram Avanzado**
- **Sistema multiusuario por PC** - cada PC tiene su código único
- **Control remoto completo** - análisis, pausa, captura de frames
- **Navegación intuitiva** con menús contextuales
- **Desconexión segura** - control total de sesiones

### 🖥️ **Sistema Multiusuario por PC**
- ✅ **Código único por PC** - cada computadora genera su código específico
- ✅ **Seguridad por autorización** - solo usuarios con código pueden acceder
- ✅ **Desconexión controlada** - usuarios pueden desconectarse cuando deseen
- ✅ **Escalabilidad total** - sin límite de PCs o usuarios

### 🎥 **Análisis Dual**
- **Tiempo Real**: Ventana en vivo con detecciones superpuestas
- **Videos**: Subida directa desde Telegram con reporte completo
- **Advertencias inteligentes** - notifica antes de cambiar modos
- **Control híbrido** - teclado + Telegram simultáneamente

## 🔐 Sistema Multiusuario - Cómo Funciona

### **1. Instalación en Nueva PC**
```bash
# Clonar o descargar proyecto
git clone [repositorio]
cd ProyectoIA-EmocionesPerros

# Instalar dependencias  
pip install -r requirements.txt

# Ejecutar por primera vez
python main.py
```

### **2. Código Único Automático**
Al ejecutar `python main.py`, el sistema:
- 🖥️ **Detecta automáticamente** el nombre de la PC
- 🔑 **Genera código único** formato: `PCNA-1234-ABCD`
- 🎨 **Muestra código colorido** en consola para fácil identificación
- 📱 **Envía mensaje de bienvenida** explicando proceso de conexión

### **3. Conexión desde Telegram**
```
1. Usuario abre Telegram
2. Busca el bot @Emocionesperrunasbot  
3. Envía /start
4. Copia código de la PC e ingresa
5. ¡Acceso autorizado!
```

### **4. Ejemplos de Códigos por PC**
- PC "LAPTOP-CASA" → Código: `LAPT-5678-WXYZ`
- PC "OFICINA-01" → Código: `OFIC-9012-QRST`  
- PC "GAMING-PC" → Código: `GAMI-3456-MNOP`

## 🚀 Instalación Rápida

### **Método 1: Archivo Ejecutable (Recomendado)**

1. **Descarga** el proyecto como ZIP
2. **Extrae** en tu carpeta deseada
3. **Doble clic** en `ejecutar.bat`
4. **Copia el código colorido** que aparece en pantalla
5. **Abre Telegram** → busca `@Emocionesperrunasbot`
6. **Envía** `/start` y luego tu código
7. **¡Listo!** Ya puedes usar todas las funciones

### **Método 2: Instalación Manual**

```cmd
# 1. Crear entorno virtual
python -m venv .venv

# 2. Activar entorno
.venv\Scripts\activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Ejecutar aplicación
python main.py
```

## 🎛️ Funciones del Bot de Telegram

### **📋 Menú Principal**
- **📹 Análisis en Tiempo Real** - Inicia cámara con ventana visual
- **🎬 Analizar Video** - Sube videos para análisis completo  
- **📊 Estado Actual** - Información del sistema en tiempo real
- **📈 Resumen del Día** - Estadísticas acumuladas
- **🔔 Activar/Pausar Monitoreo** - Alertas automáticas
- **💡 Consejos Generales** - Recomendaciones por emoción
- **🚪 Desconectar de PC** - Cerrar sesión segura
- **❓ Ayuda** - Guía completa de uso

### **🎥 Análisis en Tiempo Real**
- **▶️ Iniciar** - Abre ventana visual en PC
- **⏸️ Pausar/Reanudar** - Control remoto del análisis  
- **⏹️ Detener** - Finaliza análisis con resumen
- **📸 Capturar Frame** - Foto instantánea con análisis
- **🎬 Cambiar a Video** - Advertencia antes de cambiar modo

### **🎬 Análisis de Videos**
- **Formatos soportados**: MP4, AVI, MOV
- **Tamaño máximo**: 20MB
- **Duración máxima**: 2 minutos  
- **Procesamiento automático** con video de salida
- **Reporte completo** con estadísticas y recomendaciones

## 🔒 Seguridad y Privacidad

### **🔐 Sistema de Autorización**
- **Código por PC**: Cada computadora tiene código único
- **Autorización obligatoria**: `/start` + código requerido
- **Desconexión segura**: Botón para cerrar sesión
- **Sin límites**: Múltiples usuarios por PC, múltiples PCs

### **🚪 Control de Sesión**
```
Usuario → "Desconectar de PC"
Bot → "⚠️ Te desconectarás de [PC-NAME]. ¿Confirmar?"
Usuario → "Sí, desconectar"  
Bot → "✅ Desconectado. Usa /start + código para reconectar"
```

### **⚠️ Advertencias Inteligentes**
```
Usuario → "Analizar Video" (con tiempo real activo)
Bot → "⚠️ Análisis en tiempo real activo. ¿Pausar y continuar?"
Usuario → "Sí, pausar y analizar video"
Bot → "⏸️ Pausado. Ahora envía tu video"
```

## 🎯 Casos de Uso

### **🏠 Uso Doméstico**
- PC principal con código compartido entre familia
- Laptop personal con código privado para uso individual
- Monitoreo remoto de mascotas durante el día

### **🏢 Uso Profesional**
- **Veterinarias**: PC de recepción + PC del veterinario
- **Centros de entrenamiento**: Múltiples estaciones independientes
- **Refugios**: Monitoreo de múltiples áreas simultáneamente

### **🎓 Uso Educativo/Investigación**
- Laboratorios con múltiples PCs de análisis
- Proyectos de investigación con datos independientes
- Demostraciones en clase con control granular

## 📊 Análisis y Reportes

### **📈 Estadísticas en Tiempo Real**
- **Emociones detectadas**: Happy, Sad, Angry, Relaxed
- **Confianza promedio**: Precisión de las detecciones
- **Tiempo de análisis**: Duración total del monitoreo
- **Frames procesados**: Cantidad de imágenes analizadas

### **📋 Reportes de Video**
```
🎬 ANÁLISIS DE VIDEO COMPLETADO

📁 Video: ejemplo.mp4
🔍 Detecciones totales: 156
🎯 Emoción dominante: HAPPY (65.4%)

📊 Distribución:
😊 HAPPY: 102 (65.4%)
😌 RELAXED: 32 (20.5%)  
😢 SAD: 15 (9.6%)
😠 ANGRY: 7 (4.5%)

⚡ Confianza promedio: 87.3%
⏱️ Duración: 45 segundos
```

### **💡 Recomendaciones Automáticas**
- **😊 Happy**: Continúa con actividades que lo hacen feliz
- **😌 Relaxed**: Estado ideal, mantén el ambiente tranquilo  
- **😢 Sad**: Dedícale tiempo y verifica si está enfermo
- **😠 Angry**: Revisa ruidos fuertes, dale espacio tranquilo

## 🛠️ Estructura del Proyecto

```
ProyectoIA-EmocionesPerros/
├── 📁 utils/                    # Módulos principales
│   ├── telegram_utils.py        # Bot de Telegram completo
│   ├── cam_utils.py            # Análisis de emociones
│   └── yolo_dog_detector.py    # Detección de perros
├── 📁 modelo/                   # Red neuronal entrenada
│   └── mejor_modelo_83.h5      # Modelo 83% precisión
├── 📁 media/                   # Videos de prueba
├── main.py                     # Aplicación principal
├── procesar_video.py          # Procesador de videos
├── ejecutar.bat               # Ejecutable principal
├── ejecutar_video.bat         # Ejecutable para videos
└── requirements.txt           # Dependencias
```

## 🚨 Solución de Problemas

### **❌ "Error inicializando Telegram"**
**Solución**: Revisa conexión a internet y reinicia la aplicación

### **❌ "Cámara no encontrada"**  
**Solución**: 
- Verifica que la cámara esté conectada
- Cierra otras aplicaciones que usen la cámara
- Reinicia la aplicación

### **❌ "Código incorrecto"**
**Solución**:
- Verifica que copiaste el código completo sin espacios
- Asegúrate de usar el código de la PC correcta
- Si reiniciaste la app, se genera un código nuevo

### **🔄 Reiniciar Sistema**
Si hay problemas, simplemente:
1. Cierra la aplicación (Ctrl+C o cerrar ventana)
2. Ejecuta nuevamente `ejecutar.bat` o `python main.py`
3. Se generará un nuevo código de conexión

## 💡 Consejos de Uso

### **🎯 Para Mejores Resultados**
- **Iluminación adecuada**: Evita contraluces y sombras fuertes
- **Perro visible**: Asegúrate de que la cara del perro sea visible  
- **Distancia óptima**: 1-3 metros de la cámara
- **Estabilidad**: Mantén la cámara fija durante análisis

### **📱 Uso del Bot**
- **Mensajes claros**: El bot responde a botones, no a texto libre
- **Una función a la vez**: Termina un análisis antes de iniciar otro
- **Desconexión segura**: Usa el botón "Desconectar" antes de cerrar
- **Códigos únicos**: Cada PC necesita su propio código

## 🎉 Características Avanzadas

### **🔄 Análisis Híbrido**
- Control simultáneo desde PC (teclado) y Telegram
- Cambio fluido entre modos de análisis
- Advertencias antes de cambiar estados

### **📸 Captura Remota**
- Toma fotos instantáneas desde Telegram
- Análisis inmediato de la foto capturada
- Envío automático del resultado

### **🎨 Interfaz Visual Rica**
- Ventana en tiempo real con colores por emoción
- Códigos de conexión con formato colorido y llamativo
- Mensajes de Telegram con emojis y formato Markdown

### **🔐 Seguridad Robusta**
- Sistema de autorización por PC
- Desconexión controlada por usuario
- Códigos únicos regenerables

---

## 📞 Información del Proyecto

**Desarrollado para**: Análisis de bienestar animal usando IA  
**Tecnologías**: Python, OpenCV, TensorFlow, YOLOv8, Telegram Bot API  
**Precisión del modelo**: 83% en detección de emociones caninas  
**Compatibilidad**: Windows 10/11, Python 3.8+

---

¡Tu compañero inteligente para el cuidado y bienestar de tu mascota! 🐕❤️
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
