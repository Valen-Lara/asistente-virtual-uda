@echo off
setlocal
rem Doble clic para abrir la aplicacion. La primera vez crea el entorno virtual
rem e instala las dependencias solo: no hace falta "activate" ni usar la consola.
cd /d "%~dp0"
set "VENV_PY=.venv\Scripts\python.exe"

if exist "%VENV_PY%" goto revisar_venv

echo Primera vez: se va a preparar el entorno. Puede tardar unos minutos.
echo.
rem Hace falta Python 3.12: con versiones mas nuevas puede no haber dlib ya compilado
py -3.12 -m venv .venv >nul 2>&1
if exist "%VENV_PY%" goto instalar
python -c "import sys; sys.exit(sys.version_info[:2] != (3, 12))" >nul 2>&1
if errorlevel 1 goto sin_python
python -m venv .venv
if not exist "%VENV_PY%" goto error_instalacion
goto instalar

:revisar_venv
"%VENV_PY%" -c "import sys; sys.exit(sys.version_info[:2] != (3, 12))" >nul 2>&1
if errorlevel 1 goto venv_otra_version
rem Se prueba importar todo antes de abrir, porque pythonw no muestra los errores
"%VENV_PY%" -c "import cv2, customtkinter, face_recognition" >nul 2>&1
if not errorlevel 1 goto abrir
echo Faltan dependencias: se van a instalar. Puede tardar unos minutos.
echo.

:instalar
"%VENV_PY%" -m pip install -r requirements.txt
if errorlevel 1 goto error_instalacion
"%VENV_PY%" -m pip install --no-deps face_recognition
if errorlevel 1 goto error_instalacion
"%VENV_PY%" -c "import cv2, customtkinter, face_recognition"
if errorlevel 1 goto error_instalacion
echo.
echo Listo. Abriendo la aplicacion...

:abrir
start "" ".venv\Scripts\pythonw.exe" main.py
exit /b 0

:sin_python
echo No se encontro Python 3.12.
echo.
echo Instalalo desde https://www.python.org/downloads/release/python-31210/
echo (en el instalador marca "Add Python to PATH") y despues volve a abrir iniciar.bat.
pause
exit /b 1

:venv_otra_version
echo La carpeta .venv se creo con una version de Python distinta de 3.12.
echo Borra la carpeta .venv (esta junto a este archivo) y volve a abrir iniciar.bat.
pause
exit /b 1

:error_instalacion
echo.
echo No se pudo instalar todo. Revisa el mensaje de arriba y la conexion a internet.
echo Si sigue fallando, borra la carpeta .venv y volve a abrir iniciar.bat.
pause
exit /b 1
