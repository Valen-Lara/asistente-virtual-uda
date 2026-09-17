# Asistente Virtual — Compañero de universidad

Asistente por voz en Python que corre en consola. La idea es gestionar una sesión de estudio sin tocar el teclado ni abrir pestañas a mano: buscar conceptos, poner música de fondo, abrir el campus y controlar el tiempo.

## Funcionalidades

| Comando de voz | Qué hace |
|---|---|
| `ayuda` | Lista todos los comandos disponibles |
| `busca en Wikipedia <tema>` | Lee en voz alta un resumen del artículo |
| `busca en internet` (a secas) | Repregunta qué buscar y recién ahí busca |
| `modo estudio` | Abre YouTube y reproduce una playlist Lo-Fi predefinida |
| `abrir el campus` / `abrir Drive` / `abrir correo` | Accesos directos a las plataformas de la facultad |
| `abrir YouTube` / `abrir navegador` | Abre el sitio en el navegador por defecto |
| `qué hora es` / `qué día es` | Informa hora y fecha para controlar bloques de estudio |
| `reproducir <tema>` | Reproduce lo que le pidas en YouTube |
| `busca en internet <tema>` | Búsqueda rápida en Google |
| `necesito un descanso` / `chiste` | Cuenta un chiste corto para la pausa activa |
| `precio de la acción de <empresa>` | Cotización actual vía Yahoo Finance |
| `adiós` / `salir` | Cierra el asistente |

## Estructura

```
asistente-virtual-uda/
├── main.py           # punto de entrada: saludo y bucle principal
├── comandos.py       # una función por funcionalidad + registro de comandos
├── voz.py            # entrada y salida de voz (pyttsx3 / speech_recognition)
├── dialogo.py        # repreguntas ("¿qué querés buscar?")
├── alumno.py         # pregunta y guarda el nombre del alumno
├── config.py         # nombres, URLs, tickers y parámetros ajustables
└── requirements.txt
```

La lógica está separada en funciones modulares. Para **agregar un comando nuevo** alcanza con escribir la función en `comandos.py` y sumarla a la lista `COMANDOS`; el bucle principal no se toca.

```python
def abrir_github(pedido, crudo):
    hablar("Abriendo GitHub.")
    webbrowser.open("https://github.com/")
    return True

COMANDOS = [
    (("abrir github",), abrir_github),
    ...
]
```

## Instalación

```bash
git clone https://github.com/Valen-Lara/asistente-virtual-uda.git
cd asistente-virtual-uda

python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux / macOS
source .venv/bin/activate

pip install -r requirements.txt
```

### Si PyAudio falla al instalar

Es el problema más común, porque compila código nativo.

- **Windows:** `pip install pipwin` y después `pipwin install pyaudio`
- **Linux (Debian/Ubuntu):** `sudo apt install portaudio19-dev python3-pyaudio espeak`
- **macOS:** `brew install portaudio`

En Linux, `pyttsx3` además necesita `espeak` para que haya voz.

## Uso

```bash
# Modo normal, por micrófono
python main.py

# Modo texto: escribís los comandos por teclado (ideal para probar sin micrófono)
python main.py --texto
```

Lo primero que hace al arrancar es preguntar el nombre del alumno, y después lo usa en el saludo y en la despedida:

```
[Aconcagua] Antes de empezar, decime tu nombre.
[vos] > me llamo Ana López

[Aconcagua] Buenas tardes Ana López, soy Aconcagua. ¿En qué te puedo ayudar?
```

Los comandos de búsqueda se pueden usar de las dos maneras. Todo junto:

```
[vos] > buscar en internet partidos de Boca Juniors
[Aconcagua] Buscando partidos de Boca Juniors en internet.
```

O el comando primero y el tema después, que es más cómodo por voz:

```
[vos] > buscar en internet
[Aconcagua] ¿Qué querés buscar en internet?
[vos] > partidos de Boca Juniors
[Aconcagua] Buscando partidos de Boca Juniors en internet.
```

Sirve igual para `busca en Wikipedia` y para `reproducir`. Si no querés buscar nada, decile "nada" o "dejalo" y vuelve a esperar comandos.

Entre la repregunta y el micrófono deja 2 segundos (`PAUSA_ANTES_DE_RESPONDER` en `config.py`), para no empezar a grabar mientras todavía estás pensando qué decir.

Si no encuentra micrófono, pasa automáticamente a modo texto en lugar de romperse.

## Decisiones técnicas

- **La voz se busca por nombre, no por ID del registro.** El ejemplo original usaba una clave de `HKEY_LOCAL_MACHINE`, que solo existe en Windows. Acá se recorren las voces instaladas y se elige la primera en español, así funciona en cualquier sistema.
- **El motor de pyttsx3 se inicializa una sola vez** y se reutiliza, en lugar de crearlo en cada llamada a `hablar()`.
- **Los comandos se comparan sin acentos y en minúsculas**, para que "qué día es hoy" y "que dia es hoy" caigan en la misma función.
- **Las librerías pesadas se importan dentro de cada función.** `pywhatkit` verifica la conexión a internet al importarse y demora el arranque; así el asistente abre al instante.
- **El nombre del alumno se pregunta, no se hardcodea.** Se pide una sola vez al arrancar (`alumno.py`), se le sacan las muletillas ("me llamo", "soy") y queda disponible para cualquier comando con `nombre_alumno()`. Si el micrófono no lo entiende, lo vuelve a pedir por teclado.
- **Los comandos primero se reconocen y después piden el dato.** Si decís solo "buscar en internet", `dialogo.preguntar()` repregunta y escucha la respuesta por el mismo canal que el resto (micrófono o teclado). Antes el tema tenía que ir sí o sí en la misma frase.
- **El disparador se recorta comparando sin acentos ni mayúsculas.** El reconocedor devuelve "Buscar en internet" con mayúscula, así que el recorte literal no coincidía y terminaba buscando en Google la frase "Buscar en internet" en lugar del tema. `sacar_disparador()` ubica el disparador sobre el texto normalizado pero corta sobre el original, para no perder los acentos de lo que se busca.
- **Hay un respiro antes de escuchar la respuesta.** `pyttsx3` devuelve el control apenas termina de hablar y el micrófono abría de inmediato. Ahora espera un par de segundos, y solo por micrófono: escribiendo no tiene sentido hacer esperar.
- **Wikipedia necesita un User-Agent propio.** Wikimedia responde `403` a las consultas que llegan con el User-Agent genérico de la librería, así que el asistente se identifica con el suyo (`USER_AGENT_WIKIPEDIA` en `config.py`).
- **Todo comando falla con un mensaje hablado**, nunca con un traceback: si falta una librería o no hay internet, el asistente lo avisa y sigue escuchando.

## Posibles mejoras

- Interfaz gráfica con Tkinter
- Temporizador Pomodoro con aviso por voz
- Palabra de activación (wake word) para no escuchar todo el tiempo
- Lectura de los próximos vencimientos desde Google Calendar
