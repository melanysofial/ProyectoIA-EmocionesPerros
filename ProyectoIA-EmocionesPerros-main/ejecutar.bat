@echo off
echo 🚀 Iniciando Dog Emotion Monitor + YOLOv8...
echo =============================================

echo 🔍 Verificando entorno virtual...
if not exist .venv (
    echo ⚠️ Entorno virtual no encontrado. Creando...
    echo 📦 Creando entorno virtual Python...
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo ❌ Error: No se pudo crear el entorno virtual
        echo 💡 Asegurate de tener Python instalado
        pause
        exit /b 1
    )
    echo ✅ Entorno virtual creado
)

echo 📂 Activando entorno virtual...
call .venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo ❌ Error activando entorno virtual
    pause
    exit /b 1
)

echo 🔍 Verificando dependencias...
python -c "import ultralytics" 2>nul
if %errorlevel% neq 0 (
    echo 📦 Instalando dependencias primera vez...
    echo    Esto puede tardar unos minutos...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo ❌ Error instalando dependencias
        pause
        exit /b 1
    )
    echo ✅ Dependencias instaladas
)

echo 🐕 NOTA: La primera vez descargará YOLOv8 (~6MB)
echo      Solo detectará emociones cuando haya perros presentes
echo      Umbral de confianza: 60%%

echo 🧠 Ejecutando programa principal...
python main.py

echo 👋 Programa terminado.
pause
