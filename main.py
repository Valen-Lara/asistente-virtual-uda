"""Asistente Virtual - Compañero de universidad.

Punto de entrada. Solo se encarga del saludo y del bucle principal:
toda la lógica de cada funcionalidad vive en comandos.py.

Uso:
    python main.py            -> por micrófono
    python main.py --texto    -> escribiendo los comandos (para probar)
"""

import argparse
import datetime

from alumno import nombre_alumno, pedir_nombre
from comandos import procesar_pedido
from config import NOMBRE_ASISTENTE
from dialogo import registrar_escucha
from voz import escuchar_microfono, escuchar_teclado, hablar, hay_microfono


def saludo_inicial():
    hora = datetime.datetime.now().hour

    if hora < 6 or hora > 20:
        momento = "Buenas noches"
    elif hora < 13:
        momento = "Buen día"
    else:
        momento = "Buenas tardes"

    hablar(
        f"{momento} {nombre_alumno()}, soy {NOMBRE_ASISTENTE}. "
        "¿En qué te puedo ayudar?"
    )


def elegir_modo_escucha(forzar_texto):
    """Decide si escuchar por micrófono o por teclado."""
    if forzar_texto:
        print("Modo texto activado. Escribí los comandos y presioná Enter.")
        return escuchar_teclado

    if not hay_microfono():
        print(
            "[aviso] No encontré micrófono disponible (¿falta PyAudio?). "
            "Paso a modo texto."
        )
        return escuchar_teclado

    return escuchar_microfono


def main():
    parser = argparse.ArgumentParser(description="Asistente virtual de estudio.")
    parser.add_argument(
        "--texto",
        action="store_true",
        help="Ingresar los comandos por teclado en lugar de usar el micrófono.",
    )
    args = parser.parse_args()

    escuchar = elegir_modo_escucha(args.texto)
    # Los comandos que repreguntan ("¿qué querés buscar?") escuchan por acá.
    registrar_escucha(escuchar)

    pedir_nombre()
    saludo_inicial()
    print("(Decí 'ayuda' para ver los comandos, o 'adiós' para salir.)")

    while True:
        try:
            crudo = escuchar()
        except KeyboardInterrupt:
            print()
            hablar("Cerrando el asistente.")
            break
        except Exception as error:
            print(f"[error] Problema al escuchar: {error}")
            break

        if not crudo.strip():
            continue

        if not procesar_pedido(crudo):
            break


if __name__ == "__main__":
    main()
