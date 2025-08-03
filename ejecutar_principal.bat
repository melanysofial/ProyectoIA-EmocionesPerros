@echo off
REM ========================================
REM EJECUTOR PRINCIPAL - Monitor de Emociones Caninas
REM ========================================

echo.
echo 🐕 MONITOR DE EMOCIONES CANINAS CON IA
echo ====================================
echo.

REM Verificar si existe el entorno virtual
if not exist ".venv\Scripts\python.exe" (
    echo ⚠️  Entorno virtual no encontrado
    echo 🔧 Ejecuta primero: python -m venv .venv
    echo 🔧 Luego: .venv\Scripts\activate
    echo 🔧 Y finalmente: pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

REM Activar entorno virtual y ejecutar
echo 🚀 Activando entorno virtual y ejecutando sistema principal...
echo.

REM Usar el Python del entorno virtual
.venv\Scripts\python.exe main.py

echo.
echo 🏁 Sistema terminado
pause
