@echo off
REM Script de configuración del entorno para Dog Emotion AI

echo ========================================
echo Configurando entorno para Dog Emotion AI
echo ========================================

REM Agregar rutas de Python al PATH
set PATH=C:\Users\Erick\AppData\Roaming\Python\Scripts;%PATH%
set PYTHONPATH=C:\Users\Erick\AppData\Roaming\Python\Python313\site-packages;%PYTHONPATH%

REM Configurar TensorFlow
set TF_CPP_MIN_LOG_LEVEL=2

echo.
echo ✅ Entorno configurado correctamente
echo.
echo Ejecuta ahora: python main.py
echo.
pause
