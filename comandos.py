"""Funcionalidades del asistente.

Cada comando es una función independiente con la misma firma:

    def mi_comando(pedido, crudo) -> bool

    pedido -> texto normalizado (minúsculas y sin acentos), para comparar
    crudo  -> texto tal cual lo dijo el usuario, para buscar en internet
    return -> True para seguir escuchando, False para cerrar el asistente

Para agregar una funcionalidad nueva alcanza con escribir la función y
sumarla a la lista COMANDOS del final. No hay que tocar el bucle principal.
"""

import datetime
import webbrowser

from alumno import nombre_alumno
from config import (
    CARTERA,
    IDIOMA_CHISTES,
    IDIOMA_WIKIPEDIA,
    ORACIONES_WIKIPEDIA,
    PLAYLIST_ESTUDIO,
    SITIOS,
    USER_AGENT_WIKIPEDIA,
)
from voz import hablar, normalizar

DIAS = {
    0: "lunes",
    1: "martes",
    2: "miércoles",
    3: "jueves",
    4: "viernes",
    5: "sábado",
    6: "domingo",
}

# No uso strftime("%B") porque depende del locale del sistema
# y en muchas máquinas devuelve el mes en inglés.
MESES = {
    1: "enero",
    2: "febrero",
    3: "marzo",
    4: "abril",
    5: "mayo",
    6: "junio",
    7: "julio",
    8: "agosto",
    9: "septiembre",
    10: "octubre",
    11: "noviembre",
    12: "diciembre",
}


# --- 1. Fecha y hora ---------------------------------------------------------
def decir_dia(pedido, crudo):
    hoy = datetime.datetime.now()
    hablar(f"Hoy es {DIAS[hoy.weekday()]} {hoy.day} de {MESES[hoy.month]}.")
    return True


def decir_hora(pedido, crudo):
    ahora = datetime.datetime.now()
    hablar(f"Son las {ahora.hour} horas con {ahora.minute} minutos.")
    return True


# --- 2. Accesos directos universitarios --------------------------------------
def _abrir(clave, mensaje):
    hablar(mensaje)
    webbrowser.open(SITIOS[clave])
    return True


def abrir_campus(pedido, crudo):
    return _abrir("campus", "Abriendo el campus de la Universidad del Aconcagua.")


def abrir_drive(pedido, crudo):
    return _abrir("drive", "Abriendo tu Drive.")


def abrir_correo(pedido, crudo):
    return _abrir("correo", "Abriendo tu correo.")


def abrir_youtube(pedido, crudo):
    return _abrir("youtube", "Abriendo YouTube.")


def abrir_navegador(pedido, crudo):
    return _abrir("navegador", "Abriendo el navegador.")


# --- 3. Modo concentración ---------------------------------------------------
def modo_estudio(pedido, crudo):
    hablar("Activando modo estudio. Poné el celular boca abajo.")
    try:
        import pywhatkit

        pywhatkit.playonyt(PLAYLIST_ESTUDIO)
    except ImportError:
        hablar("Me falta la librería pywhatkit, abro YouTube directamente.")
        webbrowser.open(SITIOS["youtube"])
    except Exception:
        hablar("No pude abrir la lista de música.")
    return True


def reproducir(pedido, crudo):
    # Ojo con el orden: primero la variante más larga, si no "reproducir"
    # quedaría recortado en "r" al sacarle "reproduci".
    tema = crudo.lower()
    for disparador in ("reproducir", "reproducí", "reproduci"):
        tema = tema.replace(disparador, "")
    tema = tema.strip(" ?¿.")

    if not tema:
        hablar("¿Qué querés que reproduzca?")
        return True

    hablar(f"Reproduciendo {tema}.")
    try:
        import pywhatkit

        pywhatkit.playonyt(tema)
    except ImportError:
        hablar("Me falta pywhatkit para reproducir.")
    except Exception:
        hablar("No pude reproducir eso.")
    return True


# --- 4. Búsquedas ------------------------------------------------------------
def buscar_wikipedia(pedido, crudo):
    consulta = crudo
    for disparador in ("busca en wikipedia", "buscá en wikipedia", "busca en Wikipedia"):
        consulta = consulta.replace(disparador, "")
    consulta = consulta.strip(" ?¿.")

    if not consulta:
        hablar("¿Qué querés que busque en Wikipedia?")
        return True

    hablar(f"Buscando {consulta} en Wikipedia.")
    try:
        import wikipedia

        wikipedia.set_lang(IDIOMA_WIKIPEDIA)
        wikipedia.set_user_agent(USER_AGENT_WIKIPEDIA)
        resultado = wikipedia.summary(consulta, sentences=ORACIONES_WIKIPEDIA)
        hablar(resultado)
    except ImportError:
        hablar("Me falta la librería wikipedia.")
    except Exception as error:
        # Cubre desambiguaciones, páginas inexistentes y problemas de red.
        nombre = type(error).__name__
        if nombre == "DisambiguationError" and getattr(error, "options", None):
            hablar(f"Ese término es ambiguo. Probá con {error.options[0]}.")
        else:
            hablar("No encontré un artículo para eso.")
    return True


def buscar_internet(pedido, crudo):
    consulta = crudo
    for disparador in ("busca en internet", "buscá en internet", "buscar en internet"):
        consulta = consulta.replace(disparador, "")
    consulta = consulta.strip(" ?¿.")

    if not consulta:
        hablar("¿Qué querés que busque?")
        return True

    hablar("Buscando información.")
    try:
        import pywhatkit

        pywhatkit.search(consulta)
    except ImportError:
        webbrowser.open(f"https://www.google.com/search?q={consulta.replace(' ', '+')}")
    return True


# --- 5. Pausas activas -------------------------------------------------------
def contar_chiste(pedido, crudo):
    try:
        import pyjokes

        hablar(pyjokes.get_joke(language=IDIOMA_CHISTES))
    except ImportError:
        hablar("Me falta la librería pyjokes.")
    except Exception:
        hablar("Me quedé sin chistes, mejor tomate un vaso de agua.")
    return True


# --- 6. Cotizaciones ---------------------------------------------------------
def precio_accion(pedido, crudo):
    empresa = next((nombre for nombre in CARTERA if nombre in pedido), None)
    if empresa is None:
        disponibles = ", ".join(CARTERA)
        hablar(f"No tengo esa empresa cargada. Puedo consultar {disponibles}.")
        return True

    hablar(f"Buscando la cotización de {empresa}.")
    try:
        import yfinance as yf

        ticker = yf.Ticker(CARTERA[empresa])
        precio = getattr(ticker.fast_info, "last_price", None)
        if precio is None:
            precio = ticker.info.get("regularMarketPrice")
        hablar(f"La acción de {empresa} está a {round(float(precio), 2)} dólares.")
    except ImportError:
        hablar("Me falta la librería yfinance.")
    except Exception:
        hablar(f"No pude obtener la cotización de {empresa}.")
    return True


# --- 7. Ayuda y salida -------------------------------------------------------
def mostrar_ayuda(pedido, crudo):
    hablar("Estos son los comandos que entiendo.")
    for claves, _ in COMANDOS:
        print(f"  • {claves[0]}")
    return True


def despedirse(pedido, crudo):
    hablar(f"Nos vemos, {nombre_alumno()}. Avisame si necesitás otra cosa.")
    return False


# --- Registro de comandos ----------------------------------------------------
# El orden importa: se ejecuta el primero que coincida.
COMANDOS = [
    (("ayuda", "que podes hacer", "que sabes hacer"), mostrar_ayuda),
    (("modo estudio", "modo concentracion"), modo_estudio),
    (("busca en wikipedia", "buscar en wikipedia"), buscar_wikipedia),
    (("busca en internet", "buscar en internet"), buscar_internet),
    (("precio de la accion", "cotizacion", "cuanto vale la accion"), precio_accion),
    (("abrir el campus", "abrir campus", "campus"), abrir_campus),
    (("abrir drive", "abrir el drive", "drive"), abrir_drive),
    (("abrir correo", "abrir el correo", "abrir mail"), abrir_correo),
    (("abrir youtube", "abrir el youtube"), abrir_youtube),
    (("abrir navegador", "abrir el navegador"), abrir_navegador),
    (("que dia es", "que fecha es"), decir_dia),
    (("que hora es", "que hora"), decir_hora),
    (("reproducir", "reproduci"), reproducir),
    (("chiste", "necesito un descanso", "pausa activa"), contar_chiste),
    (("adios", "chau", "hasta luego", "salir", "terminar"), despedirse),
]


def procesar_pedido(crudo):
    """Busca el comando que corresponde y lo ejecuta.

    Devuelve True si el asistente debe seguir escuchando.
    """
    pedido = normalizar(crudo)

    for claves, accion in COMANDOS:
        if any(clave in pedido for clave in claves):
            return accion(pedido, crudo)

    hablar("No conozco ese comando. Decí 'ayuda' para ver la lista.")
    return True
