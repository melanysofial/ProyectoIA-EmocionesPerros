@echo off
REM ========================================
REM SCRIPT DE LIMPIEZA - Monitor de Emociones Caninas
REM ========================================

echo.
echo 🧹 LIMPIEZA DEL PROYECTO
echo ========================
echo.

echo 🗑️ Eliminando archivos temporales...

REM Eliminar archivos cache de Python
if exist "__pycache__" (
    rmdir /s /q "__pycache__"
    echo ✅ Eliminado: __pycache__
) else (
    echo ⚠️ No existe: __pycache__
)

if exist "utils\__pycache__" (
    rmdir /s /q "utils\__pycache__"
    echo ✅ Eliminado: utils\__pycache__
) else (
    echo ⚠️ No existe: utils\__pycache__
)

REM Eliminar archivos .pyc
for /r %%i in (*.pyc) do (
    del "%%i"
    echo ✅ Eliminado: %%i
)

REM Eliminar videos procesados temporales (opcional)
echo.
echo 📹 ¿Eliminar videos procesados temporales? (s/n)
set /p delete_videos=

if /i "%delete_videos%"=="s" (
    for %%f in (*_procesado.mp4 *_con_detecciones.mp4) do (
        if exist "%%f" (
            del "%%f"
            echo ✅ Eliminado: %%f
        )
    )
    echo ✅ Videos temporales eliminados
) else (
    echo ⚠️ Videos temporales conservados
)

REM Eliminar capturas temporales (opcional)
echo.
echo 📸 ¿Eliminar capturas temporales? (s/n)
set /p delete_captures=

if /i "%delete_captures%"=="s" (
    for %%f in (captura_*.jpg alerta_*.jpg test_*.jpg) do (
        if exist "%%f" (
            del "%%f"
            echo ✅ Eliminado: %%f
        )
    )
    echo ✅ Capturas temporales eliminadas
) else (
    echo ⚠️ Capturas temporales conservadas
)

REM Eliminar logs antiguos (opcional)
if exist "*.log" (
    echo.
    echo 📝 ¿Eliminar archivos de log? (s/n)
    set /p delete_logs=
    
    if /i "%delete_logs%"=="s" (
        del "*.log"
        echo ✅ Logs eliminados
    ) else (
        echo ⚠️ Logs conservados
    )
)

echo.
echo ✅ LIMPIEZA COMPLETADA
echo.
echo 📋 ARCHIVOS IMPORTANTES CONSERVADOS:
echo    - main.py (programa principal)
echo    - config.py (configuración)
echo    - procesar_video.py (procesamiento)
echo    - modelo/ (modelo de IA)
echo    - utils/ (utilidades)
echo    - media/ (videos de prueba)
echo    - requirements.txt (dependencias)
echo.
echo 💡 Tip: Ejecuta este script regularmente para mantener el proyecto limpio
echo.

pause
