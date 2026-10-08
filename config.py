"""Configuración general del asistente.

Todo lo que se pueda querer cambiar (nombres, URLs, tickers, idioma)
vive acá para no tener que tocar la lógica.
"""

# --- Identidad ---------------------------------------------------------------
# El nombre del alumno se pregunta al arrancar (ver alumno.py). Esto es solo
# el comodín que se usa si no llega a entenderse la respuesta.
NOMBRE_ALUMNO_POR_DEFECTO = "alumno"
NOMBRE_ASISTENTE = "Aconcagua"

# --- Voz ---------------------------------------------------------------------
# Voces neuronales de Edge TTS: suenan mucho más naturales que espeak, pero
# necesitan internet. Si no hay conexión se usa la voz del sistema (pyttsx3).
# La clave es el nombre con el que el alumno la pide ("cambiar voz" -> "Tomás").
VOCES = {
    "elena": ("es-AR-ElenaNeural", "Elena, argentina"),
    "tomas": ("es-AR-TomasNeural", "Tomás, argentino"),
    "dalia": ("es-MX-DaliaNeural", "Dalia, mexicana"),
    "jorge": ("es-MX-JorgeNeural", "Jorge, mexicano"),
    "elvira": ("es-ES-ElviraNeural", "Elvira, española"),
    "alvaro": ("es-ES-AlvaroNeural", "Álvaro, español"),
}
VOZ_POR_DEFECTO = "elena"
VELOCIDAD_VOZ_NEURAL = "+0%"  # ej. "+10%" más rápido, "-10%" más lento

# Voz de respaldo (pyttsx3 / espeak), solo si Edge TTS no está disponible.
VELOCIDAD_VOZ = 175  # palabras por minuto aprox.

# Pistas para encontrar una voz en español entre las instaladas en el sistema.
# Evita hardcodear el ID del registro de Windows (que no existe en Linux/Mac).
PISTAS_VOZ_ES = (
    "spanish",
    "español",
    "espanol",
    "helena",
    "sabina",
    "es_es",
    "es-es",
    "es_ar",
    "es-ar",
    "es_mx",
)

# --- Reconocimiento de voz ---------------------------------------------------
IDIOMA_RECONOCIMIENTO = "es-AR"
# Respiro entre que el asistente termina de preguntar algo y abre el micrófono,
# para no empezar a grabar cuando el alumno todavía está pensando qué decir.
# Solo se aplica por micrófono: escribiendo no hace falta esperar.
PAUSA_ANTES_DE_RESPONDER = 5  # segundos
PAUSA_ANTES_DE_CORTAR = 0.8   # segundos de silencio para dar por terminada la frase
ESPERA_MAXIMA = 8             # segundos esperando a que empieces a hablar
DURACION_MAXIMA_FRASE = 10    # segundos máximos de grabación por comando

# --- Contenido ---------------------------------------------------------------
IDIOMA_WIKIPEDIA = "es"
ORACIONES_WIKIPEDIA = 2

# Wikimedia responde 403 a las consultas que llegan con el User-Agent genérico
# que trae la librería, así que el asistente se identifica con uno propio.
USER_AGENT_WIKIPEDIA = f"Asistente{NOMBRE_ASISTENTE}/1.0 (proyecto universitario)"
IDIOMA_CHISTES = "es"

PLAYLIST_ESTUDIO = "lo fi hip hop radio beats to relax study to"

SITIOS = {
    "campus": "https://www.uda.edu.ar/",
    "drive": "https://drive.google.com/",
    "correo": "https://mail.google.com/",
    "youtube": "https://www.youtube.com/",
    "navegador": "https://www.google.com.ar/",
}

# Empresas soportadas para consultar cotizaciones.
CARTERA = {
    "apple": "AAPL",
    "amazon": "AMZN",
    "google": "GOOGL",
    "tesla": "TSLA",
    "microsoft": "MSFT",
    "nvidia": "NVDA",
    "mercado libre": "MELI",
}
