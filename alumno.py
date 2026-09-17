"""Nombre del alumno que está usando el asistente.

El nombre no viene fijo en config.py: se pregunta al arrancar y queda
guardado acá para que cualquier comando lo pueda usar con nombre_alumno().
"""

from config import NOMBRE_ALUMNO_POR_DEFECTO
from dialogo import preguntar
from voz import hablar, normalizar

# Muletillas que suele decir la gente al presentarse ("me llamo Juan").
PREFIJOS = ("me llamo", "mi nombre es", "yo soy", "soy")

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


def pedir_nombre():
    """Pregunta el nombre al arrancar y lo guarda."""
    global _nombre

    nombre = _limpiar(preguntar("Antes de empezar, decime tu nombre."))
    if nombre:
        _nombre = nombre
    else:
        hablar(f"No pude tomar tu nombre, te voy a decir {_nombre}.")

    return _nombre
