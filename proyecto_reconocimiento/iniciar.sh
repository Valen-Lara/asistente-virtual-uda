#!/bin/bash
# Equivalente a iniciar.bat para Linux. La primera vez crea el entorno virtual
# e instala las dependencias solo; las siguientes abre la aplicación directamente.
cd "$(dirname "$0")"
VENV_PY=".venv/bin/python"

if ! python3 -c "import tkinter" 2>/dev/null; then
    echo "Falta Tkinter. Instalalo con: sudo apt install python3-tk python3-venv"
    exit 1
fi

if [ ! -x "$VENV_PY" ]; then
    echo "Primera vez: se va a preparar el entorno. Puede tardar unos minutos."
    python3 -m venv .venv || { echo "No se pudo crear el entorno virtual."; exit 1; }
fi

# Se prueba importar todo antes de abrir
if ! "$VENV_PY" -c "import cv2, customtkinter, face_recognition" 2>/dev/null; then
    echo "Faltan dependencias: se van a instalar. Puede tardar unos minutos."
    "$VENV_PY" -m pip install -r requirements.txt \
        && "$VENV_PY" -m pip install --no-deps face_recognition \
        || { echo "No se pudo instalar todo. Revisá el mensaje de arriba y la conexión a internet."; exit 1; }
fi

exec "$VENV_PY" main.py
