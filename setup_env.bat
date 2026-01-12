@echo off
echo ============================================================
echo   INSTALACION AUTOMATICA DE ENTORNO - AUTOMATIZADOR NWS
echo ============================================================
echo.

cd /d "%~dp0"

:: 1. Verificar si Python esta instalado
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python no esta instalado o no esta en el PATH.
    echo Por favor, instala Python desde https://python.org y marca la casilla "Add Python to PATH".
    echo.
    pause
    exit /b
)

:: 2. Crear entorno virtual si no existe
if not exist ".venv" (
    echo [INFO] Creando entorno virtual nuevo (.venv)...
    python -m venv .venv
) else (
    echo [INFO] Entorno virtual ya existente.
)

:: 3. Activar entorno e instalar dependencias
echo [INFO] Instalando librerias desde requirements.txt...
call .venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt

echo.
echo ============================================================
echo   INSTALACION COMPLETADA CON EXITO
echo ============================================================
echo.
echo Ya puedes ejecutar "launch_app.bat" para usar la aplicacion.
echo.
pause
