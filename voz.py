"""Entrada y salida de voz.

Acá está todo lo que tiene que ver con hablar (pyttsx3) y escuchar
(speech_recognition). El resto del programa no sabe qué librería se usa:
solo llama a hablar() y a escuchar_microfono() / escuchar_teclado().
"""

import unicodedata

from config import (
    DURACION_MAXIMA_FRASE,
    ESPERA_MAXIMA,
    IDIOMA_RECONOCIMIENTO,
    NOMBRE_ASISTENTE,
    PAUSA_ANTES_DE_CORTAR,
    PISTAS_VOZ_ES,
    VELOCIDAD_VOZ,
)

try:
    import pyttsx3
except ImportError:  # el asistente igual funciona, pero solo por texto
    pyttsx3 = None

try:
    import speech_recognition as sr
except ImportError:
    sr = None


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


def hablar(mensaje):
    """Muestra el mensaje en consola y lo pronuncia si hay motor de voz."""
    print(f"\n[{NOMBRE_ASISTENTE}] {mensaje}")

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
