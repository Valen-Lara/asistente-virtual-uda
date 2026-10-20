import argparse

from config import ajustes
from models.cargador_imagenes import CargadorImagenesModel
from models.reconocedor_facial import ReconocedorFacialModel
from models.registro_asistencia import RegistroAsistenciaModel
from views.interfaz_video import InterfazVideoView
from controllers.app_controller import AplicacionController

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Registro de asistencia por reconocimiento facial.")
    parser.add_argument('--consola', action='store_true',
                        help="Toma asistencia en una ventana de OpenCV, sin la interfaz gráfica.")
    parser.add_argument('--comparar', nargs=2, metavar=('CONTROL', 'PRUEBA'),
                        help="Compara dos imágenes y muestra si son la misma persona.")
    args = parser.parse_args()

    # Inicializamos modelos y vista
    cargador = CargadorImagenesModel()
    reconocedor = ReconocedorFacialModel(ajustes.TOLERANCIA)
    registro = RegistroAsistenciaModel(ajustes.ARCHIVO_ASISTENCIA)
    vista = InterfazVideoView()

    # Inyectamos todo al controlador
    app = AplicacionController(cargador, reconocedor, registro, vista, ajustes)

    if args.comparar:
        app.comparar_imagenes(*args.comparar)
    elif args.consola:
        print("Iniciando cámara... Presiona 'q' en la ventana de video para salir.")
        app.iniciar()
    else:
        from views.interfaz_grafica import InterfazGraficaView
        InterfazGraficaView(app).mainloop()
