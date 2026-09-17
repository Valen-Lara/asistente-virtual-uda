"""Repreguntas del asistente.

Varios comandos necesitan pedir un dato antes de trabajar ("¿qué querés
buscar?"). El canal de escucha lo elige main.py (micrófono o teclado), así que
se registra acá una sola vez y cualquier comando puede usar preguntar().
"""

import time

from config import PAUSA_ANTES_DE_RESPONDER
from voz import escuchar_teclado, hablar, normalizar

# Formas de decir "dejá, no quiero nada": cortan la repregunta sin buscar nada.
CANCELAR = ("nada", "ninguna", "cancelar", "cancela", "olvidalo", "dejalo",
            "no importa", "nada que ver", "no", "listo")

INTENTOS = 2

_escuchar = escuchar_teclado


def registrar_escucha(escuchar):
    """main.py avisa por dónde escuchar (micrófono o teclado)."""
    global _escuchar
    _escuchar = escuchar or escuchar_teclado


def _tomarse_un_segundo(escuchar):
    """Espera un toque antes de abrir el micrófono.

    Escribiendo no tiene sentido esperar, así que en modo teclado no hace nada.
    """
    if escuchar is escuchar_teclado or PAUSA_ANTES_DE_RESPONDER <= 0:
        return
    time.sleep(PAUSA_ANTES_DE_RESPONDER)


def preguntar(mensaje):
    """Hace una pregunta y devuelve la respuesta tal cual la dijo el alumno.

    Devuelve '' si no contestó nada o si dijo que lo dejemos ahí.
    """
    escuchar = _escuchar
    hablar(mensaje)

    for intento in range(INTENTOS):
        _tomarse_un_segundo(escuchar)

        try:
            respuesta = escuchar()
        except Exception as error:
            print(f"[aviso] No pude escuchar la respuesta ({error}).")
            return ""

        respuesta = respuesta.strip(" ¿?¡!.,")

        if normalizar(respuesta) in CANCELAR:
            return ""
        if respuesta:
            return respuesta

        if intento < INTENTOS - 1:
            if escuchar is not escuchar_teclado:
                hablar("No te entendí. Escribilo y presioná Enter.")
                escuchar = escuchar_teclado
            else:
                hablar("No te entendí, repetilo por favor.")

    return ""
