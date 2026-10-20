@echo off
rem Abre la interfaz con doble clic, sin dejar una consola abierta.
cd /d "%~dp0"
if not exist ".venv\Scripts\pythonw.exe" (
    echo No encontre el entorno virtual. Segui los pasos de instalacion del README.
    pause
    exit /b 1
)
start "" ".venv\Scripts\pythonw.exe" main.py
