@echo off
:: Script para procesar videos con detección de perros y emociones
:: Uso: ejecutar_video.bat "ruta_del_video.mp4"

title Dog Emotion Monitor - Procesador de Video
color 0A

echo.
echo ===================================================
echo    🎬 DOG EMOTION MONITOR - PROCESADOR DE VIDEO    
echo ===================================================
echo.

if "%~1"=="" (
    echo ❌ Error: Debes proporcionar la ruta del video
    echo.
    echo Uso: %~n0 "ruta_del_video.mp4"
    echo.
    echo Ejemplos:
    echo   %~n0 "C:\Videos\mi_perro.mp4"
    echo   %~n0 "video_perro.avi"
    echo.
    pause
    exit /b 1
)

set VIDEO_PATH=%~1
echo 📁 Video a procesar: %VIDEO_PATH%

:: Verificar que el archivo existe
if not exist "%VIDEO_PATH%" (
    echo ❌ Error: El archivo no existe: %VIDEO_PATH%
    pause
    exit /b 1
)

echo.
echo ⚙️ Configuración:
echo   [1] Solo mostrar video procesado
echo   [2] Mostrar y guardar video procesado  
echo   [3] Solo procesar sin mostrar ^(más rápido^)
echo   [4] Procesar y enviar resumen completo por Telegram 📱
echo.
set /p OPCION="Selecciona una opción (1-4): "

:: Activar entorno conda
echo.
echo 🔧 Activando entorno Python...
call C:\Users\melan\anaconda3\envs\iacam-env-py311\python.exe --version
if errorlevel 1 (
    echo ❌ Error: No se puede activar el entorno Python
    pause
    exit /b 1
)

:: Cambiar al directorio correcto
cd /d "%~dp0"

echo.
echo 🚀 Iniciando procesamiento...
echo.

:: Ejecutar según la opción seleccionada
if "%OPCION%"=="1" (
    echo 📺 Modo: Solo mostrar
    C:\Users\melan\anaconda3\envs\iacam-env-py311\python.exe procesar_video.py "%VIDEO_PATH%"
) else if "%OPCION%"=="2" (
    echo 💾 Modo: Mostrar y guardar
    C:\Users\melan\anaconda3\envs\iacam-env-py311\python.exe procesar_video.py "%VIDEO_PATH%" --save
) else if "%OPCION%"=="3" (
    echo ⚡ Modo: Solo procesar ^(sin mostrar^)
    C:\Users\melan\anaconda3\envs\iacam-env-py311\python.exe procesar_video.py "%VIDEO_PATH%" --save --no-display
) else if "%OPCION%"=="4" (
    echo 📱 Modo: Procesar con resumen por Telegram
    echo    - Se procesará el video
    echo    - Se guardará automáticamente  
    echo    - Se enviará resumen completo por Telegram
    C:\Users\melan\anaconda3\envs\iacam-env-py311\python.exe procesar_video.py "%VIDEO_PATH%" --save
) else (
    echo ⚠️ Opción no válida, usando modo por defecto
    C:\Users\melan\anaconda3\envs\iacam-env-py311\python.exe procesar_video.py "%VIDEO_PATH%"
)

echo.
if errorlevel 1 (
    echo ❌ El procesamiento terminó con errores
) else (
    echo ✅ Procesamiento completado exitosamente
)

echo.
echo 📊 Revisa los logs arriba para ver las estadísticas
pause
