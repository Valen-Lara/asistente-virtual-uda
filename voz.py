"""Entrada y salida de voz.

Acá está todo lo que tiene que ver con hablar (edge-tts, con pyttsx3 de
respaldo) y escuchar (speech_recognition). El resto del programa no sabe qué
librería se usa: solo llama a hablar() y a escuchar_microfono() /
escuchar_teclado().
"""

import asyncio
import io
import os
import unicodedata

from config import (
    DURACION_MAXIMA_FRASE,
    ESPERA_MAXIMA,
    IDIOMA_RECONOCIMIENTO,
    NOMBRE_ASISTENTE,
    PAUSA_ANTES_DE_CORTAR,
    PISTAS_VOZ_ES,
    VELOCIDAD_VOZ,
    VELOCIDAD_VOZ_NEURAL,
    VOCES,
    VOZ_POR_DEFECTO,
)

try:
    import edge_tts

    # pygame saluda por consola al importarse; acá no queremos ese cartel.
    os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
    import pygame
except ImportError:  # sin voz neuronal: se usa la del sistema
    edge_tts = None

try:
    import pyttsx3
except ImportError:  # el asistente igual funciona, pero solo por texto
    pyttsx3 = None

try:
    import speech_recognition as sr
except ImportError:
    sr = None


def _silenciar_alsa():
    """Calla los mensajes 'ALSA lib ...' que salen al abrir el micrófono.

    En Linux, PyAudio prueba todos los dispositivos de audio y ALSA imprime
    un aviso por cada uno que no existe. No son errores, solo ensucian la
    consola. En Windows y Mac no hay ALSA, así que no hace nada.
    """
    import ctypes
    import ctypes.util

    ruta = ctypes.util.find_library("asound")
    if not ruta:
        return

    try:
        alsa = ctypes.cdll.LoadLibrary(ruta)
        tipo = ctypes.CFUNCTYPE(
            None, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p,
            ctypes.c_int, ctypes.c_char_p,
        )
        global _manejador_alsa  # si se lo lleva el recolector, se cuelga
        _manejador_alsa = tipo(lambda *args: None)
        alsa.snd_lib_error_set_handler(_manejador_alsa)
    except (OSError, AttributeError):
        pass


_silenciar_alsa()


# --- Texto -------------------------------------------------------------------
def normalizar(texto):
    """Pasa a minúsculas y saca los acentos.

    Así 'qué día es hoy' y 'que dia es hoy' matchean con la misma palabra clave.
    """
    texto = texto.lower().strip()
    sin_tildes = unicodedata.normalize("NFD", texto)
    return "".join(c for c in sin_tildes if unicodedata.category(c) != "Mn")


# --- Salida de voz -----------------------------------------------------------
_motor = None


def _elegir_voz_espanol(motor):
    """Busca entre las voces del sistema alguna en español."""
    try:
        voces = motor.getProperty("voices")
    except Exception:
        return

    for voz in voces:
        etiqueta = f"{getattr(voz, 'name', '')} {getattr(voz, 'id', '')}".lower()
        if any(pista in etiqueta for pista in PISTAS_VOZ_ES):
            motor.setProperty("voice", voz.id)
            return


def _obtener_motor():
    """Inicializa el motor una sola vez y lo reutiliza."""
    global _motor
    if _motor is None and pyttsx3 is not None:
        try:
            _motor = pyttsx3.init()
            _motor.setProperty("rate", VELOCIDAD_VOZ)
            _elegir_voz_espanol(_motor)
        except Exception as error:
            print(f"[aviso] No pude inicializar la voz ({error}). Sigo solo por texto.")
    return _motor


# --- Voz neuronal (Edge TTS) -------------------------------------------------
_voz_actual = VOZ_POR_DEFECTO
_neural_disponible = edge_tts is not None


def voz_actual():
    """Clave de la voz elegida (ver VOCES en config.py)."""
    return _voz_actual


def cambiar_voz(clave):
    """Elige otra voz de VOCES. Devuelve False si la clave no existe."""
    global _voz_actual
    if clave not in VOCES:
        return False
    _voz_actual = clave
    return True


async def _sintetizar(mensaje, voz):
    """Pide el audio a Edge TTS y lo devuelve como mp3 en memoria."""
    comunicacion = edge_tts.Communicate(mensaje, voz, rate=VELOCIDAD_VOZ_NEURAL)
    audio = io.BytesIO()
    async for fragmento in comunicacion.stream():
        if fragmento["type"] == "audio":
            audio.write(fragmento["data"])
    audio.seek(0)
    return audio


def _hablar_neural(mensaje):
    """Pronuncia con la voz neuronal. Devuelve False si no se pudo."""
    global _neural_disponible
    if not _neural_disponible:
        return False

    try:
        audio = asyncio.run(_sintetizar(mensaje, VOCES[_voz_actual][0]))
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        pygame.mixer.music.load(audio, "mp3")
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.wait(50)
        return True
    except Exception as error:
        # Casi siempre es falta de internet. Para no demorar cada respuesta
        # esperando la conexión, sigue con la voz del sistema hasta cerrar.
        print(f"[aviso] No pude usar la voz neuronal ({error}). Uso la del sistema.")
        _neural_disponible = False
        return False


def hablar(mensaje):
    """Muestra el mensaje en consola y lo pronuncia si hay motor de voz."""
    print(f"\n[{NOMBRE_ASISTENTE}] {mensaje}")

    if _hablar_neural(mensaje):
        return

    motor = _obtener_motor()
    if motor is None:
        return

    try:
        motor.say(mensaje)
        motor.runAndWait()
    except RuntimeError:
        # pyttsx3 tira esto si el loop ya estaba corriendo; no es fatal.
        pass


# --- Entrada -----------------------------------------------------------------
def hay_microfono():
    """True si están las dependencias para escuchar por micrófono."""
    if sr is None:
        return False
    try:
        sr.Microphone()
        return True
    except Exception:
        return False


def escuchar_microfono():
    """Graba un comando y lo devuelve como texto. Devuelve '' si falla."""
    if sr is None:
        raise RuntimeError("Falta instalar SpeechRecognition y PyAudio.")

    reconocedor = sr.Recognizer()
    reconocedor.pause_threshold = PAUSA_ANTES_DE_CORTAR

    with sr.Microphone() as origen:
        reconocedor.adjust_for_ambient_noise(origen, duration=0.4)
        print("\n🎙️  Escuchando...")
        try:
            audio = reconocedor.listen(
                origen,
                timeout=ESPERA_MAXIMA,
                phrase_time_limit=DURACION_MAXIMA_FRASE,
            )
        except sr.WaitTimeoutError:
            return ""

    try:
        pedido = reconocedor.recognize_google(audio, language=IDIOMA_RECONOCIMIENTO)
        print(f"[vos] {pedido}")
        return pedido
    except sr.UnknownValueError:
        print("[aviso] No te entendí, repetilo por favor.")
        return ""
    except sr.RequestError:
        print("[aviso] Sin conexión con el servicio de reconocimiento.")
        return ""


def escuchar_teclado():
    """Modo texto: sirve para probar sin micrófono ni internet."""
    try:
        return input("\n[vos] > ")
    except EOFError:
        return "adios"
