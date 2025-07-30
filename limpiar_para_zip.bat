@echo off
echo 🧹 Limpiando proyecto para compresion rapida...

echo ❌ Eliminando entorno virtual (.venv)...
if exist .venv rmdir /s /q .venv

echo ❌ Eliminando archivos de test...
if exist simple_test.py del simple_test.py
if exist test_image_quick.py del test_image_quick.py

echo ❌ Eliminando cache de Python...
for /d /r %%i in (__pycache__) do (
    if exist "%%i" rmdir /s /q "%%i"
)

echo ❌ Eliminando imagenes temporales...
if exist *.jpg del *.jpg
if exist *.png del *.png
if exist *.jpeg del *.jpeg

echo ✅ Limpieza completa!
echo 📦 El proyecto ahora es mucho mas liviano para comprimir
echo.
echo 📋 ARCHIVOS ESENCIALES MANTENIDOS:
echo    - main.py
echo    - ejecutar.bat  
echo    - get_chat_id.py
echo    - requirements.txt
echo    - README.md
echo    - modelo/mejor_modelo_83.h5
echo    - utils/ (archivos Python)
echo    - yolov8n.pt
echo.
echo 💡 Tu companero debera ejecutar: pip install -r requirements.txt
pause
