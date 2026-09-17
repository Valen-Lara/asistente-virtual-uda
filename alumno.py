"""Nombre del alumno que está usando el asistente.

El nombre no viene fijo en config.py: se pregunta al arrancar y queda
guardado acá para que cualquier comando lo pueda usar con nombre_alumno().
"""

from config import NOMBRE_ALUMNO_POR_DEFECTO
from voz import escuchar_teclado, hablar, normalizar

# Muletillas que suele decir la gente al presentarse ("me llamo Juan").
PREFIJOS = ("me llamo", "mi nombre es", "yo soy", "soy")

INTENTOS = 2

_nombre = NOMBRE_ALUMNO_POR_DEFECTO


def nombre_alumno():
    """Devuelve el nombre cargado (o el genérico si nunca se preguntó)."""
    return _nombre


def _limpiar(respuesta):
    """Saca signos y muletillas. Devuelve '' si no quedó un nombre usable."""
    limpio = respuesta.strip(" ¿?¡!.,")

    sin_tildes = normalizar(limpio)
    for prefijo in PREFIJOS:
        if sin_tildes.startswith(prefijo):
            limpio = limpio[len(prefijo):].strip()
            break

    if not any(caracter.isalpha() for caracter in limpio):
        return ""

    return limpio.title()


def pedir_nombre(escuchar=None):
    """Pregunta el nombre y lo guarda. Si no lo entiende, pasa a teclado."""
    global _nombre

    if escuchar is None:
        escuchar = escuchar_teclado

    hablar("Antes de empezar, decime tu nombre.")

    for intento in range(INTENTOS):
        try:
            respuesta = escuchar()
        except Exception as error:
            print(f"[aviso] No pude escuchar el nombre ({error}).")
            respuesta = ""

        nombre = _limpiar(respuesta)
        if nombre:
            _nombre = nombre
            return _nombre

        if intento < INTENTOS - 1:
            if escuchar is not escuchar_teclado:
                hablar("No te entendí. Escribí tu nombre y presioná Enter.")
                escuchar = escuchar_teclado
            else:
                hablar("No te entendí, repetilo por favor.")

    hablar(f"No pude tomar tu nombre, te voy a decir {_nombre}.")
    return _nombre
