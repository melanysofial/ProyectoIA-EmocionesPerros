@echo off
REM ============================================================
REM Dog Emotion AI - Script de Ejecución Optimizado
REM ============================================================
REM Este script configura el entorno y ejecuta la aplicación
REM de manera óptima para Python 3.13 con instalaciones de usuario
REM ============================================================

setlocal enabledelayedexpansion

REM Colores para la consola
color 0A

REM Título de la ventana
title Dog Emotion AI - Análisis Emocional de Mascotas

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                    🐕 DOG EMOTION AI 🐕                       ║
echo ║              Análisis Emocional de Mascotas con IA            ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

REM Detectar Python
echo [1/5] 🔍 Detectando Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ ERROR: Python no está instalado o no está en el PATH
    echo 💡 Instala Python 3.8+ desde https://python.org
    pause
    exit /b 1
)

REM Mostrar versión de Python
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo ✅ Python %PYTHON_VERSION% detectado

REM Obtener rutas de Python
echo [2/5] 📂 Configurando rutas de Python...
for /f "delims=" %%i in ('python -c "import site; print(site.USER_BASE)"') do set USER_BASE=%%i
for /f "delims=" %%i in ('python -c "import site; print(site.USER_SITE)"') do set USER_SITE=%%i

REM Configurar variables de entorno
echo [3/5] 🔧 Configurando entorno...
set PATH=%USER_BASE%\Scripts;%PATH%
set PYTHONPATH=%USER_SITE%;%PYTHONPATH%

REM Configurar TensorFlow para reducir warnings
set TF_CPP_MIN_LOG_LEVEL=2

REM Desactivar advertencias de protobuf
set PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python

echo ✅ Entorno configurado correctamente

REM Verificar si es primera ejecución
if not exist "cache\first_run_complete.txt" (
    echo [4/5] 🚀 Primera ejecución detectada...
    echo.
    echo 📦 Verificando dependencias...
    python fix_dependencies.py
    
    REM Marcar como ejecutado
    if not exist cache mkdir cache
    echo %date% %time% > cache\first_run_complete.txt
) else (
    echo [4/5] ✅ Configuración previa detectada
)

REM Ejecutar la aplicación
echo [5/5] 🌐 Iniciando aplicación web...
echo.
echo ============================================================
echo 🌐 La aplicación se abrirá en: http://localhost:5000
echo ⚠️  Presiona Ctrl+C para detener el servidor
echo ============================================================
echo.

REM Ejecutar con manejo de errores
python main.py
if errorlevel 1 (
    echo.
    echo ❌ La aplicación terminó con errores
    echo.
    echo 💡 Posibles soluciones:
    echo    1. Ejecuta: python fix_dependencies.py
    echo    2. Reinstala dependencias: pip install --user -r requirements.txt
    echo    3. Revisa el archivo logs\dog_emotion_ai.log
    echo.
    pause
) else (
    echo.
    echo ✅ Aplicación cerrada correctamente
    echo.
    timeout /t 3
)

endlocal